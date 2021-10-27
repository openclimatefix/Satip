import pandas as pd

from typing import Union, Any

import os
import subprocess
import zarr
import xarray as xr
from satpy import Scene
from pathlib import Path
import datetime
from satip.geospatial import lat_lon_to_osgb, GEOGRAPHIC_BOUNDS
from satip.compression import Compressor, is_dataset_clean
import warnings

warnings.filterwarnings("ignore", message="divide by zero encountered in true_divide")
warnings.filterwarnings("ignore", message="invalid value encountered in sin")
warnings.filterwarnings("ignore", message="invalid value encountered in cos")
warnings.filterwarnings(
    "ignore",
    message="You will likely lose important projection information when converting to a PROJ string from another format. See: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems",
)


def decompress(full_bzip_filename: Path, temp_pth: Path) -> str:
    """
    Decompresses .bz2 file and returns the non-compressed filename

    Args:
        full_bzip_filename: Full compressed filename
        temp_pth: Temporary path to save the native file

    Returns:
        The full native filename to the decompressed file
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


def load_native_to_dataset(filename: Path, area: str) -> Union[xr.DataArray, None]:
    """
    Load compressed native files into an Xarray dataset, resampling to the same grid for the HRV channel,
     and replacing small chunks of NaNs with interpolated values, and add a time coordinate
    Args:
        filename: The filename of the compressed native file to load
        area: Name of the geographic area to use, such as 'UK'

    Returns:
        Returns Xarray DataArray if script worked, else returns None
    """
    compressor = Compressor()
    temp_directory = filename.parent
    try:
        # IF decompression fails, pass
        decompressed_filename: str = decompress(filename, temp_directory)
    except subprocess.CalledProcessError:
        return None
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
    # HRV is the only one different than the others, so to make it simpler, resample all to HRV resolution (3x the resolution)
    scene = scene.resample()

    # HRV covers a smaller portion of the disk than other bands, so use that as the bounds
    # Selected bounds emprically for have no NaN values from off disk image, and covering the UK + a bit
    scene = scene.crop(ll_bbox=GEOGRAPHIC_BOUNDS[area])

    # Lat and Lon are the same for all the channels now
    lon, lat = scene["HRV"].attrs["area"].get_lonlats()
    osgb_x, osgb_y = lat_lon_to_osgb(lat, lon)
    dataset: xr.Dataset = scene.to_xarray_dataset()
    # Add coordinate arrays, since x and y changes for each pixel, cannot replace dataset x,y coords with these directly
    dataset.attrs["osgb_x_coords"] = osgb_x
    dataset.attrs["osgb_y_coords"] = osgb_y
    # Round to the nearest 5 minutes
    dataset.attrs["end_time"] = pd.Timestamp(dataset.attrs["end_time"]).round("5 min")

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


get_time_as_unix = (
    lambda da: pd.Series(
        (pd.to_datetime(da.time.values) - pd.Timestamp("1970-01-01")).total_seconds()
    )
    .astype(int)
    .values
)


def save_dataset_to_zarr(
    dataarray: xr.DataArray,
    zarr_path: str,
    zarr_mode: str = "a",
    timesteps_per_chunk: int = 1,
    y_size_per_chunk: int = 256,
    x_size_per_chunk: int = 256,
) -> None:
    """
    Save an Xarray DataArray into a Zarr file

    Args:
        dataarray: DataArray to save
        zarr_path: Filename of the Zarr dataset
        zarr_mode: Mode to write to the filename, either 'w' for write, or 'a' to append
        timesteps_per_chunk: Timesteps per Zarr chunk
        y_size_per_chunk: Y pixels per Zarr chunk
        x_size_per_chunk: X pixels per Zarr chunk

    """
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

    dataarray.to_zarr(zarr_path, mode=zarr_mode, consolidated=True, **extra_kwargs)


def add_constant_coord_to_dataarray(
    dataarray: xr.DataArray, coord_name: str, coord_val: Any
) -> xr.DataArray:
    """
    Adds a new coordinate with a constant value to the DataArray

    Args:
        dataarray: DataArrray which will have the new coords added to it
        coord_name: Name for the new coordinate dimensions
        coord_val: Value that will be assigned to the new coordinates

    Returns:
        DataArrray with the new coords added to it
    """
    dataarray = dataarray.assign_coords({coord_name: coord_val}).expand_dims(coord_name)

    return dataarray


def check_if_timestep_exists(dt: datetime.datetime, zarr_dataset: xr.Dataset) -> bool:
    """
    Check if a timestep exists within the Xarray dataset

    Args:
        dt: Datetime of the file to check
        zarr_dataset: Zarr dataset ofthe EUMETSAT data

    Returns:
        Bool whether the timestep is in the Xarray 'time' coordinate or not
    """
    dt = int((dt - pd.Timestamp("1970-01-01")).total_seconds())
    if dt in zarr_dataset.coords["time"].values:
        return True
    else:
        return False
