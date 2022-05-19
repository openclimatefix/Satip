"""Utilities module to handle data and logging.

Collection of helper functions and utilities around
- data loading/saving
- data conversion
- data sanitation
- setting up a logger
- datetime string formatting
"""

import datetime
import logging
import os
import subprocess
import tempfile
import warnings
from pathlib import Path
from typing import Any, Tuple

import fsspec
import numcodecs
import numpy as np
import pandas as pd
import xarray as xr
import zarr
from satpy import Scene

from satip.geospatial import GEOGRAPHIC_BOUNDS, lat_lon_to_osgb
from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs
from satip.scale_to_zero_to_one import ScaleToZeroToOne, compress_mask
from satip.serialize import serialize_attrs

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", message="divide by zero encountered in true_divide")
warnings.filterwarnings("ignore", message="invalid value encountered in sin")
warnings.filterwarnings("ignore", message="invalid value encountered in cos")
warnings.filterwarnings("ignore", message="invalid value encountered in double_scalars")
warnings.filterwarnings("ignore", message="invalid value encountered in true_divide")
warnings.filterwarnings(
    "ignore",
    message=(
        "You will likely lose important projection information when converting "
        "to a PROJ string from another format. See: https://proj.org/faq.html"
        "#what-is-the-best-format-for-describing-coordinate-reference-systems"
    ),
)


def format_dt_str(datetime_string):
    """Helper function to get a consistently formatted string."""
    return pd.to_datetime(datetime_string).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def load_native_to_dataarray(
    filename: Path, temp_directory: Path, area: str, calculate_osgb: bool = True
) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Load compressed native files into an Xarray dataset

    Resampling to the same grid for the HRV channel,
     and replacing small chunks of NaNs with interpolated values, and add a time coordinate

    Args:
        filename: The filename of the compressed native file to load
        temp_directory: Temporary directory to store the decompressed files
        area: Name of the geographic area to use, such as 'UK'
        calculate_osgb: Whether to calculate OSGB x and y coordinates,
                        only needed for first data array

    Returns:
        Returns Xarray DataArray if script worked, else returns None
    """
    hrv_scaler = ScaleToZeroToOne(
        variable_order=["HRV"], maxs=np.array([103.90016]), mins=np.array([-1.2278595])
    )
    scaler = ScaleToZeroToOne(
        mins=np.array(
            [
                -2.5118103,
                -64.83977,
                63.404694,
                2.844452,
                199.10002,
                -17.254883,
                -26.29155,
                -1.1009827,
                -2.4184198,
                199.57048,
                198.95093,
            ]
        ),
        maxs=np.array(
            [
                69.60857,
                339.15588,
                340.26526,
                317.86752,
                313.2767,
                315.99194,
                274.82297,
                93.786545,
                101.34922,
                249.91806,
                286.96323,
            ]
        ),
        variable_order=[
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
        ],
    )
    if filename.suffix == ".bz2":
        try:
            # IF decompression fails, pass
            decompressed_filename: str = decompress(filename, temp_directory)
            decompressed_file = True
        except subprocess.CalledProcessError:
            return None, None
    else:
        decompressed_filename = str(filename)
        decompressed_file = False
    scene = Scene(filenames={"seviri_l1b_native": [decompressed_filename]})
    hrv_scene = Scene(filenames={"seviri_l1b_native": [decompressed_filename]})
    hrv_scene.load(
        [
            "HRV",
        ]
    )
    scene.load(
        [
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
    # HRV covers a smaller portion of the disk than other bands, so use that as the bounds
    # Selected bounds empirically for have no NaN values from off disk image,
    # and are covering the UK + a bit
    dataarray: xr.DataArray = convert_scene_to_dataarray(
        scene, band="IR_016", area=area, calculate_osgb=calculate_osgb
    )
    hrv_dataarray: xr.DataArray = convert_scene_to_dataarray(
        hrv_scene, band="HRV", area=area, calculate_osgb=calculate_osgb
    )
    if decompressed_file:
        # Delete file off disk, but only if we decompressed it first, so still have a copy
        os.remove(decompressed_filename)

    # Compress and return
    dataarray = scaler.rescale(dataarray)
    hrv_dataarray = hrv_scaler.rescale(hrv_dataarray)
    return dataarray, hrv_dataarray


# TODO: temp_directory is unused and has no effect. But for the sake of interface consistency
# with load_native_to_dataset, can also stay.
def load_cloudmask_to_dataarray(
    filename: Path, temp_directory: Path, area: str, calculate_osgb: bool = True
) -> xr.DataArray:
    """
    Load cloud mask files into an Xarray dataset

    Replacing small chunks of NaNs with interpolated values, and add a time coordinate

    Args:
        filename: The filename of the GRIB file to load
        temp_directory: Temporary directory to store the decompressed files
        area: Name of the geographic area to use, such as 'UK'
        calculate_osgb: Whether to calculate OSGB x and y coordinates,
                        only needed for first data array

    Returns:
        Returns Xarray DataArray if script worked, else returns None
    """
    scene = Scene(filenames={"seviri_l2_grib": [filename]})
    scene.load(
        [
            "cloud_mask",
        ]
    )
    try:
        # Selected bounds empirically that have no NaN values from off disk image,
        # and are covering the UK + a bit
        dataarray: xr.DataArray = convert_scene_to_dataarray(
            scene, band="cloud_mask", area=area, calculate_osgb=calculate_osgb
        )
        return compress_mask(dataarray)
    except Exception:
        return None


def convert_scene_to_dataarray(
    scene: Scene, band: str, area: str, calculate_osgb: bool = True
) -> xr.DataArray:
    """
    Convertes a Scene with satellite data into a data array.

    Args:
        scene: The satpy.Scene containing the satellite data
        band: The name of the band
        area: Name of the geographic area to use, such as 'UK'
        calculate_osgb: Whether to calculate OSGB x and y coordinates,
                        only needed for first data array

    Returns:
        Returns Xarray DataArray
    """
    if area not in GEOGRAPHIC_BOUNDS:
        raise ValueError(f"`area` must be one of {GEOGRAPHIC_BOUNDS.keys()}, not '{area}'")
    if area != "RSS":
        scene = scene.crop(ll_bbox=GEOGRAPHIC_BOUNDS[area])

    # Remove acq time from all bands because it is not useful, and can actually
    # get in the way of combining multiple Zarr datasets.
    data_attrs = {}
    for channel in scene.wishlist:
        scene[channel] = scene[channel].drop_vars("acq_time", errors="ignore")
        for attr in scene[channel].attrs:
            new_name = channel["name"] + "_" + attr
            data_attrs[new_name] = scene[channel].attrs[attr]
    dataset: xr.Dataset = scene.to_xarray_dataset()
    dataarray = dataset.to_array()

    # Lat and Lon are the same for all the channels now
    if calculate_osgb:
        lon, lat = scene[band].attrs["area"].get_lonlats()
        osgb_x, osgb_y = lat_lon_to_osgb(lat, lon)
        # Assign x_osgb and y_osgb and set some attributes
        dataarray = dataarray.assign_coords(
            x_osgb=(("y", "x"), np.float32(osgb_x)),
            y_osgb=(("y", "x"), np.float32(osgb_y)),
        )
        for name in ["x_osgb", "y_osgb"]:
            dataarray[name].attrs = {
                "units": "meter",
                "coordinate_reference_system": "OSGB",
            }

        dataarray.x_osgb.attrs["name"] = "Easting"
        dataarray.y_osgb.attrs["name"] = "Northing"

    for name in ["x", "y"]:
        dataarray[name].attrs["coordinate_reference_system"] = "geostationary"

    # Round to the nearest 5 minutes
    dataarray.attrs.update(data_attrs)
    dataarray.attrs["end_time"] = pd.Timestamp(dataarray.attrs["end_time"]).round("5 min")

    # Rename x and y to make clear the coordinate system they are in
    dataarray = dataarray.rename({"x": "x_geostationary", "y": "y_geostationary"})
    if "time" not in dataarray.dims:
        time = pd.to_datetime(pd.Timestamp(dataarray.attrs["end_time"]).round("5 min"))
        dataarray = add_constant_coord_to_dataarray(dataarray, "time", time)

    del dataarray["crs"]
    del scene

    return dataarray


def save_native_to_netcdf(
    list_of_native_files: list,
    bands: list = [
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
    ],
    save_dir: str = "./",
    use_rescaler: bool = False,
) -> None:
    """
    Saves native files to NetCDF for consumer

    Args:
        list_of_native_files: List of native files to convert into a single NetCDF file
        bands: Bands to save
        save_dir: Directory to save the netcdf files
        use_rescaler: Whether to rescale between 0 and 1 or not
    """

    logger.info(f"Converting from native to netcdf in {save_dir}")

    scaler = ScaleToZeroToOne(
        mins=np.array(
            [
                -2.5118103,
                -64.83977,
                63.404694,
                2.844452,
                199.10002,
                -17.254883,
                -26.29155,
                -1.1009827,
                -2.4184198,
                199.57048,
                198.95093,
            ]
        ),
        maxs=np.array(
            [
                69.60857,
                339.15588,
                340.26526,
                317.86752,
                313.2767,
                315.99194,
                274.82297,
                93.786545,
                101.34922,
                249.91806,
                286.96323,
            ]
        ),
        variable_order=[
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
        ],
    )
    hrv_scaler = ScaleToZeroToOne(
        variable_order=["HRV"], maxs=np.array([103.90016]), mins=np.array([-1.2278595])
    )
    for f in list_of_native_files:

        logger.debug(f"Processing {f}")

        if "HRV" in bands:
            logger.debug("Processing HRV")

            hrv_scene = Scene(filenames={"seviri_l1b_native": [f]})
            hrv_scene.load(
                [
                    "HRV",
                ]
            )
            hrv_dataarray: xr.DataArray = convert_scene_to_dataarray(
                hrv_scene, band="HRV", area="UK", calculate_osgb=True
            )
            attrs = serialize_attrs(hrv_dataarray.attrs)
            if use_rescaler:
                hrv_dataarray = hrv_scaler.rescale(hrv_dataarray)
            else:
                hrv_dataarray = hrv_dataarray.reindex({"variable": ["HRV"]}).transpose(
                    "time", "y_geostationary", "x_geostationary", "variable"
                )
                hrv_dataarray = hrv_dataarray.astype(np.float32)
            hrv_dataarray = hrv_dataarray.transpose(
                "time", "y_geostationary", "x_geostationary", "variable"
            )
            hrv_dataset = hrv_dataarray.to_dataset(name="data")
            hrv_dataset.attrs.update(attrs)
            now_time = pd.Timestamp(hrv_dataset["time"].values[0]).strftime("%Y%m%d%H%M")
            save_file = os.path.join(save_dir, f"hrv_{now_time}.zarr.zip")
            logger.info(f"Saving HRV netcdf in {save_file}")
            save_to_zarr_to_s3(hrv_dataset, save_file)

        logger.debug("Processing non-HRV")
        scene = Scene(filenames={"seviri_l1b_native": [f]})
        scene.load(
            [
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
        dataarray: xr.DataArray = convert_scene_to_dataarray(
            scene, band="IR_016", area="UK", calculate_osgb=True
        )
        attrs = serialize_attrs(dataarray.attrs)
        if use_rescaler:
            dataarray = scaler.rescale(dataarray)
        else:
            dataarray = dataarray.reindex(
                {
                    "variable": [
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
                }
            ).transpose("time", "y_geostationary", "x_geostationary", "variable")
            dataarray = dataarray.astype(np.float32)
        dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")
        dataset = dataarray.to_dataset(name="data")
        dataset.attrs.update(attrs)
        now_time = pd.Timestamp(dataset["time"].values[0]).strftime("%Y%m%d%H%M")
        save_file = os.path.join(save_dir, f"{now_time}.zarr.zip")
        logger.info(f"Saving non-HRV netcdf in {save_file}")
        save_to_zarr_to_s3(dataset, save_file)


def save_dataarray_to_zarr(
    dataarray: xr.DataArray,
    zarr_path: str,
    compressor_name: str,
    zarr_mode: str = "a",
    timesteps_per_chunk: int = 1,
    y_size_per_chunk: int = 256,
    x_size_per_chunk: int = 256,
    channel_chunk_size: int = 1,
) -> None:
    """
    Save an Xarray DataArray into a Zarr file

    Args:
        dataarray: DataArray to save
        zarr_path: Filename of the Zarr dataset
        compressor_name: The name of the compression algorithm to use. Must be 'bz2' or 'jpeg-xl'.
        zarr_mode: Mode to write to the filename, either 'w' for write, or 'a' to append
        timesteps_per_chunk: Timesteps per Zarr chunk
        y_size_per_chunk: Y pixels per Zarr chunk
        x_size_per_chunk: X pixels per Zarr chunk
        channel_chunk_size: Chunk size for the Dask arrays. Must be 1 whilst using JPEG-XL
          (at least until imagecodecs implements decompressing JPEG-XL files with multiple
          images per file.)
    """
    dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")

    # Number of timesteps, x and y size per chunk, and channels (all 12)
    chunks = (
        timesteps_per_chunk,
        x_size_per_chunk,
        y_size_per_chunk,
        channel_chunk_size,
    )
    dataarray = dataarray.chunk(chunks)

    compression_algos = {
        "bz2": numcodecs.get_codec(dict(id="bz2", level=5)),
        "jpeg-xl": JpegXlFloatWithNaNs(lossless=False, distance=0.4, effort=8),
    }
    compression_algo = compression_algos[compressor_name]

    zarr_mode_to_extra_kwargs = {
        "a": {"append_dim": "time"},
        "w": {
            "encoding": {
                "data": {
                    "compressor": compression_algo,
                    "chunks": chunks,
                },
                "time": {"units": "nanoseconds since 1970-01-01"},
            }
        },
    }

    assert zarr_mode in ["a", "w"], "`zarr_mode` must be one of: `a`, `w`"
    extra_kwargs = zarr_mode_to_extra_kwargs[zarr_mode]

    dataset = dataarray.to_dataset(name="data")
    dataset.to_zarr(zarr_path, mode=zarr_mode, consolidated=True, compute=True, **extra_kwargs)


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
    dt = pd.Timestamp(dt).round("5 min")
    if dt in zarr_dataset.coords["time"].dt.round("5 min").values:
        return True
    else:
        return False


def create_markdown_table(table_info: dict, index_name: str = "Id") -> str:
    """
    Returns a formatted string for a markdown table, according to the dictionary passed as `table_info`.  # noqa E501

    Args:
        table_info: Mapping from index to values
        index_name: Name to use for the index column

    Returns:
        md_str: Markdown formatted table string

    Example:
        >>> table_info = {
                'Apples': {
                    'Cost': '40p',
                    'Colour': 'Red/green',
                },
                'Oranges': {
                    'Cost': '50p',
                    'Colour': 'Orange',
                },
            }
        >>> md_str = create_markdown_table(table_info, index_name='Fruit')
        >>> print(md_str)
        | Fruit   | Cost   | Colour    |
        |:--------|:-------|:----------|
        | Apples  | 40p    | Red/green |
        | Oranges | 50p    | Orange    |
    """

    df_info = pd.DataFrame(table_info).T
    df_info.index.name = index_name

    md_str = df_info.to_markdown()

    return md_str


def save_to_zarr_to_s3(dataset: xr.Dataset, filename: str):
    """Save xarray to netcdf in s3

    1. Save in temp local dir
    2. upload to s3
    :param dataset: The Xarray Dataset to be save
    :param filename: The s3 filname
    """
    with tempfile.TemporaryDirectory() as dir:
        # save locally
        path = f"{dir}/temp.zarr.zip"
        with zarr.ZipStore(path) as store:
            dataset.to_zarr(store, compute=True, mode="w")

        # save to s3
        filesystem = fsspec.open(filename).fs
        filesystem.put(path, filename)


def filter_dataset_ids_on_current_files(datasets: list, save_dir: str) -> list:
    """
    Filter dataset ids on files in a directory

    The following occurs:
    1. get ids of files that will be downloaded
    2. get datetimes of already downloaded files
    3. only keep indexes where we need to download them

    Args:
        datasets: list of datasets with ids
        save_dir: The directory where files wil be saved

    Returns:
        The filtered list of new datasets ids to download
    """
    from satip.eumetsat import eumetsat_filename_to_datetime

    ids = [dataset["id"] for dataset in datasets]
    filesystem = fsspec.open(save_dir).fs
    finished_files = filesystem.glob(f"{save_dir}/*.zarr.zip")
    datetimes = [pd.Timestamp(eumetsat_filename_to_datetime(idx)).round("5 min") for idx in ids]
    if not datetimes:  # Empty list
        logger.debug("No datetimes to download")
        return []
    logger.debug(f"The latest datetime that we want to downloaded is {max(datetimes)}")

    finished_datetimes = []

    # get datetimes of the finished files
    for date in finished_files:
        finished_datetimes.append(
            pd.to_datetime(
                date.split(".zarr.zip")[0].split("/")[-1], format="%Y%m%d%H%M", errors="ignore"
            )
        )
    if len(finished_datetimes) > 0:
        logger.debug(f"The already downloaded finished datetime are {finished_datetimes}")
    else:
        logger.debug("There are no files already downloaded")

    # find which indexes to remove, if file is already there
    idx_to_remove = []
    for idx, date in enumerate(datetimes):
        if date in finished_datetimes:
            idx_to_remove.append(idx)
    logger.debug(
        f"Will be not be downloading {len(idx_to_remove)} files "
        f"as they have already been downloaded"
    )

    # remove index
    indices = sorted(idx_to_remove, reverse=True)
    for idx in indices:
        if idx < len(datasets):
            datasets.pop(idx)
    return datasets


def move_older_files_to_different_location(save_dir: str, history_time: pd.Timestamp):
    """
    Move older files in save_dir to a different location

    Args:
        save_dir: Directory where data is being saved
        history_time: History time to keep files

    """
    filesystem = fsspec.open(save_dir).fs

    # Now to move into latest
    finished_files = filesystem.glob(f"{save_dir}/*.zarr.zip")

    logger.info(f"Checking {save_dir}/ for moving newer files into {save_dir}/latest/")

    # get datetimes of the finished files
    for date in finished_files:
        if "latest.zarr" in date or "tmp" in date:
            continue
        if "hrv" in date:
            file_time = pd.to_datetime(
                date.split(".zarr.zip")[0].split("/")[-1].split("_")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
                utc=True,
            )
        else:
            file_time = pd.to_datetime(
                date.split(".zarr.zip")[0].split("/")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
                utc=True,
            )
        if file_time > history_time:
            # Move HRV and non-HRV to new place
            filesystem.move(date, f"{save_dir}/latest/{date.split('/')[-1]}")
        elif file_time < (history_time - pd.Timedelta("2 days")):
            # Delete files over 2 days old
            filesystem.rm(date)

    finished_files = filesystem.glob(f"{save_dir}/latest/*.zarr.zip")
    logger.info(f"Checking {save_dir}/latest/ for older files")
    # get datetimes of the finished files
    for date in finished_files:
        if "latest.zarr" in date or "tmp" in date:
            continue
        if "hrv" in date:
            file_time = pd.to_datetime(
                date.split(".zarr.zip")[0].split("/")[-1].split("_")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
                utc=True,
            )
        else:
            file_time = pd.to_datetime(
                date.split(".zarr.zip")[0].split("/")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
                utc=True,
            )
        if file_time < history_time:
            # Move HRV and non-HRV to new place
            filesystem.move(date, f"{save_dir}/{date.split('/')[-1]}")


def collate_files_into_latest(save_dir: str):
    """
    Convert individual files into single latest file for HRV and non-HRV

    Args:
        save_dir: Directory where data is being saved

    """
    filesystem = fsspec.open(save_dir).fs
    hrv_files = list(filesystem.glob(f"{save_dir}/latest/hrv_2*.zarr.zip"))
    if not hrv_files:  # Empty set of files, don't do anything
        return
    # Add S3 to beginning of each URL
    hrv_files = ["zip:///::s3://" + str(f) for f in hrv_files]
    dataset = xr.open_mfdataset(
        hrv_files, concat_dim="time", combine="nested", engine="zarr"
    ).sortby("time")
    save_to_zarr_to_s3(dataset, f"{save_dir}/latest/hrv_tmp.zarr.zip")
    nonhrv_files = list(filesystem.glob(f"{save_dir}/latest/2*.zarr.zip"))
    nonhrv_files = ["zip:///::s3://" + str(f) for f in nonhrv_files]
    o_dataset = xr.open_mfdataset(
        nonhrv_files, concat_dim="time", combine="nested", engine="zarr"
    ).sortby("time")
    save_to_zarr_to_s3(o_dataset, f"{save_dir}/latest/tmp.zarr.zip")
    filesystem = fsspec.open(f"{save_dir}/latest/hrv_tmp.zarr.zip").fs
    filesystem.mv(f"{save_dir}/latest/hrv_tmp.zarr.zip", f"{save_dir}/latest/hrv_latest.zarr.zip")
    logger.info(f"Collating HRV into {save_dir}/latest/hrv_latest.zarr.zip")
    filesystem = fsspec.open(f"{save_dir}/latest/tmp.zarr.zip").fs
    filesystem.mv(f"{save_dir}/latest/tmp.zarr.zip", f"{save_dir}/latest/latest.zarr.zip")
    logger.info(f"Collating non-HRV into {save_dir}/latest/latest.zarr.zip")


# Cell
def set_up_logging(
    name: str,
    main_logging_level: str = "DEBUG",
) -> logging.Logger:
    """`set_up_logging` initialises and configures a custom logger for `satip`.

    The custom logger's logging level of the file and
    Jupyter outputs are specified by `main_logging_level`
    whilst the Slack handler uses `slack_logging_level`.
    There are three core ways that logs are broadcasted:
    - Logging to a specified file
    - Logging to Jupyter cell outputs
    - Logging to Slack
    Note that the value passed for `main_logging_level`
    and `slack_logging_level` must be one of:
    - 'CRITICAL'
    - 'FATAL'
    - 'ERROR'
    - 'WARNING'
    - 'WARN'
    - 'INFO'
    - 'DEBUG'
    - 'NOTSET'
    Parameters:
        name: Name of the logger, if a logging.Logger object
              is passed then that will be used instead.
        log_dir: directory where the logs will be stored
        main_logging_level: Logging level for file and Jupyter
    Returns:
        logger: Custom satip logger
    Example:
        Here we'll create a custom logger that saves data
        to the file 'test_log.txt' and also sends Slack
        messages to the specified user and channel.
        >>> from satip.utils import set_up_logging
        >>> import logging
        >>> logger = set_up_logging(
                'test_log',
                'test_log.txt',
                slack_id=slack_id,
                slack_webhook_url=slack_webhook_url
            )
        >>> logger.log(
                logging.INFO,
                'This will output to file and Jupyter but not to Slack as it is not critical'
            )
        '2020-10-20 10:24:35,367 - INFO - This will output to file and Jupyter but not to Slack as it is not critical'  # noqa: E501
    """

    # Initialising logger
    if isinstance(name, str):
        logger = logging.getLogger(name)
    else:
        # instance where a logger object is passed
        logger = name

    # Configuring log level
    logging_levels = [
        "CRITICAL",
        "FATAL",
        "ERROR",
        "WARNING",
        "WARN",
        "INFO",
        "DEBUG",
        "NOTSET",
    ]

    assert (
        main_logging_level in logging_levels
    ), f"main_logging_level must be one of {', '.join(logging_levels)}"

    logger.setLevel(getattr(logging, main_logging_level))

    # Defining global formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Configuring Jupyter output handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
