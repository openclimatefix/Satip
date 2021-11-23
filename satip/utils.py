import datetime
import logging
import os
import subprocess
import warnings
from pathlib import Path
from typing import Any, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr
import zarr
from satpy import Scene

from satip.compression import Compressor, is_dataset_clean
from satip.geospatial import GEOGRAPHIC_BOUNDS, lat_lon_to_osgb

warnings.filterwarnings("ignore", message="divide by zero encountered in true_divide")
warnings.filterwarnings("ignore", message="invalid value encountered in sin")
warnings.filterwarnings("ignore", message="invalid value encountered in cos")
warnings.filterwarnings("ignore", message="invalid value encountered in double_scalars")
warnings.filterwarnings("ignore", message="invalid value encountered in true_divide")
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


def load_native_to_dataset(
    filename: Path, temp_directory: Path, area: str
) -> Union[Tuple[xr.DataArray, xr.DataArray], Tuple[None, None]]:
    """
    Load compressed native files into an Xarray dataset, resampling to the same grid for the HRV channel,
     and replacing small chunks of NaNs with interpolated values, and add a time coordinate
    Args:
        filename: The filename of the compressed native file to load
        temp_directory: Temporary directory to store the decompressed files
        area: Name of the geographic area to use, such as 'UK'

    Returns:
        Returns Xarray DataArray if script worked, else returns None
    """
    hrv_compressor = Compressor(
        variable_order=["HRV"], maxs=np.array([103.90016]), mins=np.array([-1.2278595])
    )
    compressor = Compressor(
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
    try:
        # IF decompression fails, pass
        decompressed_filename: str = decompress(filename, temp_directory)
    except subprocess.CalledProcessError:
        return None, None
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
    # Selected bounds emprically for have no NaN values from off disk image, and covering the UK + a bit
    dataarray: xr.DataArray = convert_scene_to_dataarray(scene, band="IR_016", area=area)
    hrv_dataarray: xr.DataArray = convert_scene_to_dataarray(hrv_scene, band="HRV", area=area)
    # Delete file off disk
    os.remove(decompressed_filename)

    # If any NaNs still exist, then don't return it
    if is_dataset_clean(dataarray) and is_dataset_clean(hrv_dataarray):
        # Compress and return
        dataarray = compressor.compress(dataarray)
        hrv_dataarray = hrv_compressor.compress(hrv_dataarray)
        return dataarray, hrv_dataarray
    else:
        return None, None


def convert_scene_to_dataarray(scene: Scene, band: str, area: str) -> xr.DataArray:
    scene = scene.crop(ll_bbox=GEOGRAPHIC_BOUNDS[area])
    # Lat and Lon are the same for all the channels now
    lon, lat = scene[band].attrs["area"].get_lonlats()
    osgb_x, osgb_y = lat_lon_to_osgb(lat, lon)
    dataset: xr.Dataset = scene.to_xarray_dataset()
    osgb_y = osgb_y[:, 0]
    osgb_x = osgb_x[0, :]
    dataset = dataset.assign_coords(x=osgb_x, y=osgb_y)
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

    return dataarray


get_time_as_unix = lambda da: pd.Series(pd.to_datetime(da.time.values)).values


def save_dataset_to_zarr(
    dataarray: xr.DataArray,
    zarr_path: str,
    zarr_mode: str = "a",
    timesteps_per_chunk: int = 1,
    y_size_per_chunk: int = 256,
    x_size_per_chunk: int = 256,
    channel_chunk_size: int = 12,
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
    # We convert the datetime to seconds since the Unix epoch as otherwise appending to the Zarr store results in the
    # first timestep being duplicated, and the actual timestep being thrown away.
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
        x_size_per_chunk,
        y_size_per_chunk,
        channel_chunk_size,
    )
    dataarray = dataarray.chunk(chunks)
    if not is_dataset_clean(dataarray):
        # One last check again just incase chunking causes any issues
        print("Failing clean check after chunking")
        return
    dataarray = dataarray.fillna(-1)  # Fill NaN with -1, even if none should exist
    dataarray = xr.Dataset({"stacked_eumetsat_data": dataarray})

    zarr_mode_to_extra_kwargs = {
        "a": {"append_dim": "time"},
        "w": {
            "encoding": {
                "stacked_eumetsat_data": {
                    "compressor": zarr.Blosc(cname="zstd", clevel=5),
                    "chunks": chunks,
                },
                "time": {"units": "nanoseconds since 1970-01-01"},
            }
        },
    }

    assert zarr_mode in ["a", "w"], "`zarr_mode` must be one of: `a`, `w`"
    extra_kwargs = zarr_mode_to_extra_kwargs[zarr_mode]

    dataarray.to_zarr(zarr_path, mode=zarr_mode, consolidated=True, compute=True, **extra_kwargs)


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


def create_markdown_table(table_info: dict, index_name: str = "Id") -> str:
    """
    Returns a string for a markdown table, formatted
    according to the dictionary passed as `table_info`
    Parameters:
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


# Cell
def set_up_logging(
    name: str,
    log_dir: str,
    main_logging_level: str = "DEBUG",
) -> logging.Logger:
    """
    `set_up_logging` initialises and configures a custom
    logger for `satip`. The logging level of the file and
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
        >>> logger = set_up_logging('test_log',
                                    'test_log.txt',
                                    slack_id=slack_id,
                                    slack_webhook_url=slack_webhook_url)
        >>> logger.log(logging.INFO, 'This will output to file and Jupyter but not to Slack as it is not critical')
        '2020-10-20 10:24:35,367 - INFO - This will output to file and Jupyter but not to Slack as it is not critical'
    """

    # Initialising logger
    if isinstance(name, str):
        logger = logging.getLogger(name)
    else:
        # instance where a logger object is passed
        logger = name

    # Configuring log level
    logging_levels = ["CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "INFO", "DEBUG", "NOTSET"]

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

    # Configuring file output handler
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_fp = f"{log_dir}/{name}.txt"
    file_handler = logging.FileHandler(log_fp, mode="a")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, main_logging_level))
    logger.addHandler(file_handler)

    return logger
