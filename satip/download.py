############
# Pull raw satellite data from EUMetSat
#
# 2021-09-28
# Jacob Bieker
#
############

import logging
import math
import multiprocessing
import os
import subprocess
import time
from datetime import datetime, timedelta
from itertools import repeat
from typing import Callable, List, Optional, Tuple

import fsspec
import numpy as np
import pandas as pd
import requests.exceptions
import yaml

from satip import eumetsat

_LOG = logging.getLogger("satip.download")
_LOG.setLevel(logging.INFO)

SAT_VARIABLE_NAMES = (
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
)

NATIVE_FILESIZE_MB = 102.210123
CLOUD_FILESIZE_MB = 3.445185
RSS_ID = "EO:EUM:DAT:MSG:MSG15-RSS"
CLOUD_ID = "EO:EUM:DAT:MSG:RSS-CLM"

format_dt_str = lambda dt: pd.to_datetime(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def download_eumetsat_data(
    download_directory,
    start_date: str,
    end_date: str,
    backfill: bool = False,
    bandwidth_limit: Optional[float] = None,
    user_key: Optional[str] = None,
    user_secret: Optional[str] = None,
    auth_filename: Optional[str] = None,
    number_of_processes: int = 0,
):
    """
    Downloads EUMETSAT RSS and Cloud Masks to the given directory,
     checking first to see if the requested files are already downloaded

    Args:
        download_directory: Directory to download the files and store them
        start_date: Start date, in a format accepted by pandas to_datetime()
        end_date: End date, in a format accepted by pandas to_datetime()
        backfill: Whether to backfill between the beginning of EUMETSAT data and now, overrides start and end date
        bandwidth_limit: Bandwidth limit, currently unused
        user_key: User key for the EUMETSAT API
        user_secret: User secret for the EUMETSAT API
        auth_filename: Path to a file containing the user_secret and user_key

    """
    # Get authentication
    if auth_filename is not None:
        if (user_key is not None) or (user_secret is not None):
            raise RuntimeError("Please do not set BOTH auth_filename AND user_key or user_secret!")
        user_key, user_secret = load_key_secret(auth_filename)

    if backfill:
        # Set to year before data started to ensure gets everything
        # No downside to requesting an earlier time
        start_date = format_dt_str("2008-01-01")
        # Set to current date to get everything up until this script started
        end_date = datetime.now()

    # Download the data
    dm = eumetsat.DownloadManager(user_key, user_secret, download_directory, download_directory)

    for product_id in [
        RSS_ID,
        CLOUD_ID,
    ]:
        # Do this to clear out any partially downloaded days
        sanity_check_files_and_move_to_directory(
            directory=download_directory, product_id=product_id
        )

        times_to_use = determine_datetimes_to_download_files(
            download_directory, start_date, end_date, product_id=product_id
        )
        _LOG.info(times_to_use)

        if number_of_processes > 0:
            pool = multiprocessing.Pool(processes=number_of_processes)
            for _ in pool.imap_unordered(
                download_time_range,
                zip(
                    reversed(times_to_use),
                    repeat(product_id),
                    repeat(dm),
                ),
            ):
                # As soon as a day is done, start doing sanity checks and moving it along
                sanity_check_files_and_move_to_directory(
                    directory=download_directory, product_id=product_id
                )
        else:
            # Want to go from most recent into the past
            for time_range in reversed(times_to_use):
                inputs = [time_range, product_id, dm]
                download_time_range(inputs)
                # Sanity check, able to open/right size and move to correct directory
                sanity_check_files_and_move_to_directory(
                    directory=download_directory, product_id=product_id
                )


def download_time_range(x: Tuple[Tuple[datetime, datetime], str, eumetsat.DownloadManager]) -> None:
    time_range, product_id, download_manager = x
    start_time, end_time = time_range
    _LOG.info(format_dt_str(start_time))
    _LOG.info(format_dt_str(end_time))
    # To help stop with rate limiting
    time.sleep(np.random.randint(0, 30))
    try:
        download_manager.download_date_range(
            format_dt_str(start_time),
            format_dt_str(end_time),
            product_id=product_id,
        )
    except requests.exceptions.ConnectionError:
        # Retry again after 10 minutes, should then continue working if intermittent
        time.sleep(600)
        download_manager.download_date_range(
            format_dt_str(start_time),
            format_dt_str(end_time),
            product_id=product_id,
        )
    except Exception as e:
        _LOG.warning(f"An Error was thrown, waiting and trying again: {e}")
        # Wait between 10 and 20 minutes and try again
        time.sleep(np.random.randint(600, 1200))
        download_manager.download_date_range(
            format_dt_str(start_time),
            format_dt_str(end_time),
            product_id=product_id,
        )


def load_key_secret(filename: str) -> Tuple[str, str]:
    """
    Load user secret and key stored in a yaml file

    Args:
        filename: Filename to read

    Returns:
        The user secret and key

    """
    with fsspec.open(filename, mode="r") as f:
        keys = yaml.load(f, Loader=yaml.FullLoader)
        return keys["key"], keys["secret"]


def sanity_check_files_and_move_to_directory(directory: str, product_id: str) -> None:
    """
    Runs a sanity check for all the files of a given product_id in the directory
    Deletes incomplete files, moves checked files to final location

    This does a sanity check by:
        Checking the filesize of RSS images
        Attempting to open them in SatPy

    While loading the file should be somewhat slow, it ensures the file can be opened

    Args:
        directory: Directory where the native files were downloaded
        product_id: The product ID of the files to check

    Returns:
        The number of incomplete files deleted
    """
    pattern = "*.nat" if product_id == RSS_ID else "*.grb"
    fs: fsspec.AbstractFileSystem = fsspec.open(directory).fs
    new_files = fs.glob(os.path.join(directory, pattern))

    date_func = (
        eumetsat_native_filename_to_datetime
        if product_id == RSS_ID
        else eumetsat_cloud_name_to_datetime
    )
    if product_id == RSS_ID:
        pool = multiprocessing.Pool()  # Use as many CPU cores as possible
        results = pool.starmap_async(
            process_rss_images, zip(new_files, repeat(directory), repeat(fs), repeat(date_func))
        )
        results.wait()
    else:
        for f in new_files:
            base_name = get_basename(f)
            file_date = date_func(base_name)
            file_size = eumetsat.get_filesize_megabytes(f)
            if not math.isclose(file_size, CLOUD_FILESIZE_MB, abs_tol=1):
                # Removes if not the right size
                _LOG.exception(
                    f"Error when sanity-checking {f}.  Skipping this file.  Will be downloaded next time this script is run."
                )
                continue
            else:
                if not fs.exists(os.path.join(directory, file_date.strftime(format="%Y/%m/%d"))):
                    fs.mkdir(os.path.join(directory, file_date.strftime(format="%Y/%m/%d")))
                # Only move if the correct size
                fs.move(
                    f, os.path.join(directory, file_date.strftime(format="%Y/%m/%d"), base_name)
                )


def process_rss_images(
    f: str, directory: str, fs: fsspec.AbstractFileSystem, date_func: Callable
) -> None:
    try:
        file_size = eumetsat.get_filesize_megabytes(f)
        if not math.isclose(file_size, NATIVE_FILESIZE_MB, abs_tol=1):
            _LOG.info("RSS Image has the wrong size, skipping")
            return
        # Now that the file has been checked and can be open, compress it and move it to the final directory
        completed_process = subprocess.run(["pbzip2", "-5", f])
        try:
            completed_process.check_returncode()
        except:
            _LOG.exception("Compression failed!")
            return
        full_compressed_filename = f + ".bz2"
        base_name = get_basename(full_compressed_filename)
        file_date = date_func(base_name)
        # Want to move it 1 minute in the future to correct the difference
        file_date = file_date + timedelta(minutes=1)
        if not fs.exists(os.path.join(directory, file_date.strftime(format="%Y/%m/%d"))):
            fs.mkdir(os.path.join(directory, file_date.strftime(format="%Y/%m/%d")))
        # Move the compressed file
        fs.move(
            full_compressed_filename,
            os.path.join(directory, file_date.strftime(format="%Y/%m/%d"), base_name),
        )
        # Remove the uncompressed file
        try:
            fs.rm(f)
        except:
            return
    except Exception as e:
        _LOG.exception(
            f"Error {e} when sanity-checking {f}.  Deleting this file.  Will be downloaded next time this script is run."
        )
        # Something is wrong with the file, redownload later
        try:
            fs.rm(f)
        except:
            return


def determine_datetimes_to_download_files(
    directory: str,
    start_date: datetime,
    end_date: datetime,
    product_id: str,
) -> List[Tuple[datetime, datetime]]:
    """
    Check the given directory, and sub-directories, for all downloaded files.

    Args:
        directory: The top-level directory to check in
        start_date: Start date as a datetime object
        end_date: End date as a datetime object
        product_id: String of the EUMETSAT product ID

    Returns:
        List of tuples of datetimes giving the ranges of time to download

    """
    # This is .bz2 as they should all be compressed files
    pattern = "*.bz2" if product_id == RSS_ID else "*.grb"
    # Get all days from start_date to end_date
    day_split = pd.date_range(start_date, end_date, freq="D")

    # Go through files and get all examples in each
    fs = fsspec.open(directory).fs

    # Go through each directory, and for each day, list any missing data
    missing_rss_timesteps = []
    for day in day_split:
        day_string = day.strftime(format="%Y/%m/%d")
        rss_images = fs.glob(os.path.join(directory, day_string, pattern))
        if len(rss_images) > 0:
            missing_rss_timesteps = (
                missing_rss_timesteps + get_missing_datetimes_from_list_of_files(rss_images)
            )
        else:
            # No files, so whole day should be included
            # Each one is at the start of the day, this then needs 1 minute before for the RSS image
            # End 2 minutes before the end of the day, as that image would be for midnight, the next day
            missing_day = (
                day - timedelta(minutes=1),
                day + timedelta(hours=23, minutes=58),
            )
            missing_rss_timesteps.append(missing_day)

    return missing_rss_timesteps


def eumetsat_native_filename_to_datetime(filename: str) -> datetime:
    """Takes a file from the EUMETSAT API and returns
    the date and time part of the filename"""
    return eumetsat.eumetsat_filename_to_datetime(filename).replace(second=0)


def eumetsat_cloud_name_to_datetime(filename: str) -> datetime:
    return eumetsat.eumetsat_cloud_name_to_datetime(filename).replace(second=0)


def get_basename(filename: str) -> str:
    return filename.split("/")[-1]


def get_missing_datetimes_from_list_of_files(
    filenames: List[str],
) -> List[Tuple[datetime, datetime]]:
    """
    Get a list of all datetimes not covered by the set of images
    Args:
        filenames: Filenames of the EUMETSAT Native files or Cloud Masks

    Returns:
        List of datetime ranges that are missing from the filename range
    """
    # Sort in order from earliest to latest
    filenames = sorted(filenames)
    is_rss = ".nat" in filenames[0]  # Which type of file it is
    func = eumetsat_native_filename_to_datetime if is_rss else eumetsat_cloud_name_to_datetime
    current_time = func(get_basename(filenames[0]))
    # Want it to be from the beginning to the end of the day, so set current time to start of day
    current_time = current_time.replace(hour=0, minute=0, second=0)
    # Start from first one and go through, adding date range between each one, as long as difference is
    # greater than or equal to 5min
    missing_date_ranges = []
    five_minutes = timedelta(minutes=5)
    for i in range(len(filenames)):
        next_time = func(get_basename(filenames[i]))
        time_difference = next_time - current_time
        if time_difference > five_minutes:
            # Add breaks to list, only want the ones between, so add 5 minutes to the start
            # In the case its missing only a single timestep, start and end would be the same time
            missing_date_ranges.append((current_time, next_time))
        current_time = next_time

    # Check the end of the day too, 2 minutes from midnight because of the RSS image at 23:59 is for the next day
    end_day = current_time.replace(hour=23, minute=58)
    if end_day - current_time > five_minutes:
        missing_date_ranges.append((current_time, end_day))
    return missing_date_ranges
