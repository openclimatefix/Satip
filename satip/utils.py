__all__ = ["create_markdown_table", "set_up_logging"]

import pandas as pd

import logging

import os
import subprocess
import zarr
import xarray as xr
from satpy import Scene
import datetime
import re


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


def load_native_to_dataset(filename: str, temp_directory: str) -> xr.Dataset:
    """
    Load compressed native files into an Xarray dataset, resampling to the same grid for the HRV channel,
     and replacing small chunks of NaNs with interpolated values, and add a time coordinate
    Args:
        filename:

    Returns:

    """

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
    dataset = scene.resample().to_xarray_dataset()

    # Round to the nearest 5 minutes
    dataset.attrs["start_time"] = round_datetime_to_nearest_5_minutes(dataset.attrs["start_time"])
    dataset.attrs["end_time"] = round_datetime_to_nearest_5_minutes(dataset.attrs["end_time"])

    # Assign the end time as the time coordinate
    dataset = dataset.assign_coords(time=dataset.attrs["end_time"])

    # Fill NaN's but only if its a short amount of NaNs
    # NaN's for off-disk would not be filled
    dataset = dataset.interpolate_na(dim="x", max_gap=2, use_coordinate=False).interpolate_na(
        dim="y", max_gap=2
    )
    return dataset


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


# xr.concat(reprojected_dss, "time", coords="all", data_vars="all")


def save_dataset_to_zarr(
    dataset: xr.Dataset,
    zarr_filename: str,
    dim_order: list = ["time", "x", "y", "variable"],
    zarr_mode: str = "a",
    timesteps_per_chunk: int = 3,
    y_size_per_chunk: int = 256,
    x_size_per_chunk: int = 256,
) -> xr.Dataset:
    dataset = dataset.transpose(*dim_order)

    # Number of timesteps, x and y size per chunk, and channels (all 12)
    chunks = {
        "time": timesteps_per_chunk,
        "y": y_size_per_chunk,
        "x": x_size_per_chunk,
        "variable": 12,
    }

    dataset = xr.Dataset({"stacked_eumetsat_data": dataset.chunk(chunks)})

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

    dataset.to_zarr(zarr_filename, mode=zarr_mode, consolidated=True, **extra_kwargs)

    return dataset


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
