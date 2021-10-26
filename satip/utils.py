__all__ = ["create_markdown_table", "set_up_logging"]

import numpy as np
import pandas as pd

import logging
from typing import Union, Tuple, Any

import os
import subprocess
import zarr
import xarray as xr
from satpy import Scene
import datetime
from satip.geospatial import lat_lon_to_osgb
from satip.compression import Compressor
import warnings

# Cell
warnings.filterwarnings("ignore", message="divide by zero encountered in true_divide")
warnings.filterwarnings("ignore", message="invalid value encountered in sin")
warnings.filterwarnings("ignore", message="invalid value encountered in cos")
warnings.filterwarnings(
    "ignore",
    message="You will likely lose important projection information when converting to a PROJ string from another format. See: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems",
)


def decompress(full_bzip_filename: str, temp_pth: str) -> str:
    """
    Decompresses .bz2 file and returns the non-compressed filename

    Args:
        full_bzip_filename:
        temp_pth:

    Returns:

    """
    base_bzip_filename = os.path.basename(full_bzip_filename)
    base_nat_filename = os.path.splitext(base_bzip_filename)[0]
    full_nat_filename = os.path.join(temp_pth, base_nat_filename)
    if os.path.exists(full_nat_filename):
        os.remove(full_nat_filename)
    with open(full_nat_filename, "wb") as nat_file_handler:
        process = subprocess.run(
            ["pbzip2", "--decompress", "--keep", "--stdout", full_bzip_filename],
            stdout=nat_file_handler,
        )
    process.check_returncode()
    return full_nat_filename


def load_native_to_dataset(filename_and_temp: Tuple[str, str]) -> Union[xr.DataArray, None]:
    """
    Load compressed native files into an Xarray dataset, resampling to the same grid for the HRV channel,
     and replacing small chunks of NaNs with interpolated values, and add a time coordinate
    Args:
        filename:

    Returns:

    """
    compressor = Compressor()
    filename, temp_directory = filename_and_temp
    decompressed_filename: str = decompress(filename, temp_directory)
    scene = Scene(filenames={"seviri_l1b_native": [decompressed_filename]})
    scene.load(
        [
            "HRV",
            "IR_016",
            "IR_039",
            "IR_087",
            "IR_097",
            "IR_108",
            "IR_120",
            "IR_134",
            "VIS006",
            "VIS008",
            "WV_062",
            "WV_073",
        ]
    )
    # While we wnat to avoid resampling as much as possible,
    # HRV is the only one different than the others, so to make it simpler, make all the same
    scene = scene.resample()
    # Lat and Lon are the same for all the channels now
    # HRV covers a smaller portion of the disk than other bands, so use that as the bounds
    # Selected bounds emprically for have no NaN values from off disk image, and covering the UK + a bit
    scene = scene.crop(ll_bbox=(-16, 45, 10, 62.5))
    lon, lat = scene["HRV"].attrs["area"].get_lonlats()
    osgb_x, osgb_y = lat_lon_to_osgb(lat, lon)
    dataset: xr.Dataset = scene.to_xarray_dataset()
    # Add coordinate arrays, since x and y changes for each pixel, cannot replace dataset x,y coords with these directly
    dataset.attrs["osgb_x_coords"] = osgb_x
    dataset.attrs["osgb_y_coords"] = osgb_y
    # Round to the nearest 5 minutes
    dataset.attrs["end_time"] = round_datetime_to_nearest_5_minutes(dataset.attrs["end_time"])

    # Stack DataArrays in the Dataset into a single DataArray
    dataarray = dataset.to_array()
    if "time" not in dataarray.dims:
        time = pd.to_datetime(dataset.attrs["end_time"])
        dataarray = add_constant_coord_to_dataarray(dataarray, "time", time)

    del dataarray["crs"]

    # Fill NaN's but only if its a short amount of NaNs
    # NaN's for off-disk would not be filled
    dataarray = dataarray.interpolate_na(dim="x", max_gap=2, use_coordinate=False).interpolate_na(
        dim="y", max_gap=2
    )

    # Delete file off disk
    os.remove(decompressed_filename)

    # If any NaNs still exist, then don't return it
    if is_dataset_clean(dataarray):
        # Compress and return
        dataarray = compressor.compress(dataarray)
        return dataarray
    else:
        return None


def is_dataset_clean(dataarray: xr.DataArray) -> bool:
    """
    Checks if all the data values in a Dataset are not NaNs

    Args:
        dataarray: Xarray dataset containing the data to check

    Returns:
        Bool of whether the dataset is clean or not
    """
    return bool((dataarray != np.NAN).all())


def round_datetime_to_nearest_5_minutes(tm: datetime.datetime) -> datetime.datetime:
    """
    Rounds a datetime to the nearest 5 minutes

    Args:
        tm: Datetime to round

    Returns:
        The rounded datetime
    """
    tm = tm.replace(second=0, microsecond=0)
    discard = datetime.timedelta(minutes=tm.minute % 5)
    tm -= discard
    if discard >= datetime.timedelta(minutes=2, seconds=30):
        tm += datetime.timedelta(minutes=5)
    return tm


get_time_as_unix = (
    lambda da: pd.Series(
        (pd.to_datetime(da.time.values) - pd.Timestamp("1970-01-01")).total_seconds()
    )
    .astype(int)
    .values
)


def save_dataset_to_zarr(
    dataarray: xr.DataArray,
    zarr_filename: str,
    zarr_mode: str = "a",
    timesteps_per_chunk: int = 1,
    y_size_per_chunk: int = 256,
    x_size_per_chunk: int = 256,
) -> xr.Dataset:
    dataarray = dataarray.transpose(*["time", "x", "y", "variable"])
    dataarray["time"] = get_time_as_unix(dataarray)

    _, x_size, y_size, _ = dataarray.shape
    # If less than 2 chunks worth, just save the whole spatial extant
    if y_size_per_chunk < y_size // 2:
        y_size_per_chunk = y_size
    if x_size_per_chunk < x_size // 2:
        x_size_per_chunk = x_size

    # Number of timesteps, x and y size per chunk, and channels (all 12)
    chunks = (
        timesteps_per_chunk,
        y_size_per_chunk,
        x_size_per_chunk,
        12,
    )

    dataarray = xr.Dataset({"stacked_eumetsat_data": dataarray.chunk(chunks)})

    zarr_mode_to_extra_kwargs = {
        "a": {"append_dim": "time"},
        "w": {
            "encoding": {
                "stacked_eumetsat_data": {
                    "compressor": zarr.Blosc(cname="zstd", clevel=5),
                    "chunks": chunks,
                }
            }
        },
    }

    assert zarr_mode in ["a", "w"], "`zarr_mode` must be one of: `a`, `w`"
    extra_kwargs = zarr_mode_to_extra_kwargs[zarr_mode]

    dataarray.to_zarr(zarr_filename, mode=zarr_mode, consolidated=True, **extra_kwargs)

    return dataarray


def add_constant_coord_to_dataarray(
    dataarray: xr.DataArray, coord_name: str, coord_val: Any
) -> xr.DataArray:
    """
    Adds a new coordinate with a
    constant value to the DataArray
    Parameters
    ----------
    dataarray : xr.DataArray
        DataArrray which will have the new coords added to it
    coord_name : str
        Name for the new coordinate dimensions
    coord_val
        Value that will be assigned to the new coordinates
    Returns
    -------
    da : xr.DataArray
        DataArrray with the new coords added to it
    """

    dataarray = dataarray.assign_coords({coord_name: coord_val}).expand_dims(coord_name)

    return dataarray


def check_if_timestep_exists(dt: datetime.datetime, zarr_dataset: xr.Dataset) -> bool:
    try:
        print(zarr_dataset.coords["time"])
        print(dt)
        time_check: xr.Dataset = zarr_dataset.sel(time=dt)
        # Only a single element should be there for the shape, and time dimension is the first one
        print(time_check)
        return 1 == time_check.data_vars["stacked_eumetsat_data"].shape[0]
    except KeyError:
        # Doesn't exist, so need this timestep
        return False
