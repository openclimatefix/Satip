"""Tests for satip.eumetsat."""
import glob
import os
from pathlib import Path

import pandas as pd
import xarray as xr

from satip import eumetsat
from satip.eumetsat import eumetsat_cloud_name_to_datetime, eumetsat_filename_to_datetime
from satip.utils import (
    check_if_timestep_exists,
    load_cloudmask_to_dataset,
    load_native_to_dataset,
    save_dataset_to_zarr,
)

RSS_ID = "EO:EUM:DAT:MSG:MSG15-RSS"
CLOUD_ID = "EO:EUM:DAT:MSG:RSS-CLM"

user_key = os.environ.get("EUMETSAT_USER_KEY")
user_secret = os.environ.get("EUMETSAT_USER_SECRET")


def test_filename_to_datetime():
    """If there were a test here, there would also be a docstring here."""
    pass


def test_data_tailor():
    """If there were a test here, there would also be a docstring here."""
    pass


def test_datetime_check_native():
    """ "Check that checking datetime works"""
    download_manager = eumetsat.DownloadManager(
        user_key=user_key,
        user_secret=user_secret,
        data_dir=os.getcwd(),
        log_fp=os.path.join(os.getcwd(), "log.txt"),
        logger_name="Plotting_test",
    )
    download_manager.download_date_range(
        start_date="2020-06-01 11:59:00", end_date="2020-06-01 12:00:00", product_id=RSS_ID
    )
    rss_filename = list(glob.glob(os.path.join(os.getcwd(), "*.nat")))
    rss_dataset, hrv_dataset = load_native_to_dataset(
        Path(rss_filename[0]), temp_directory=Path(os.getcwd()), area="UK"
    )

    # Save to Zarrs, to then load them back
    save_dataset_to_zarr(
        rss_dataset,
        zarr_path=os.path.join(os.getcwd(), "rss.zarr"),
        channel_chunk_size=11,
        dtype="int16",
        zarr_mode="w",
    )
    save_dataset_to_zarr(
        hrv_dataset,
        zarr_path=os.path.join(os.getcwd(), "hrv.zarr"),
        channel_chunk_size=1,
        dtype="int16",
        zarr_mode="w",
    )

    zarr_dataset = xr.open_zarr(os.path.join(os.getcwd(), "rss.zarr"), consolidated=True)
    base_filename = Path(rss_filename[0]).name
    file_timestep = eumetsat_filename_to_datetime(str(base_filename))
    assert check_if_timestep_exists(pd.Timestamp(file_timestep).round("5 min"), zarr_dataset)
    zarr_dataset = xr.open_zarr(os.path.join(os.getcwd(), "hrv.zarr"), consolidated=True)
    assert check_if_timestep_exists(pd.Timestamp(file_timestep).round("5 min"), zarr_dataset)


def test_datetime_check_cloud_mask():
    """ "Check that checking datetime works"""
    download_manager = eumetsat.DownloadManager(
        user_key=user_key,
        user_secret=user_secret,
        data_dir=os.getcwd(),
        log_fp=os.path.join(os.getcwd(), "log.txt"),
        logger_name="Plotting_test",
    )
    download_manager.download_date_range(
        start_date="2020-06-01 11:59:00", end_date="2020-06-01 12:00:00", product_id=CLOUD_ID
    )
    cloud_mask_filename = list(glob.glob(os.path.join(os.getcwd(), "*.grb")))
    cloudmask_dataset = load_cloudmask_to_dataset(
        Path(cloud_mask_filename[0]), temp_directory=Path(os.getcwd()), area="UK"
    )

    # Save to Zarrs, to then load them back
    save_dataset_to_zarr(
        cloudmask_dataset,
        zarr_path=os.path.join(os.getcwd(), "cloud.zarr"),
        channel_chunk_size=1,
        dtype="int8",
        zarr_mode="w",
    )

    zarr_dataset = xr.open_zarr(os.path.join(os.getcwd(), "cloud.zarr"), consolidated=True)
    base_filename = Path(cloud_mask_filename[0]).name
    file_timestep = eumetsat_cloud_name_to_datetime(str(base_filename))
    assert check_if_timestep_exists(pd.Timestamp(file_timestep).round("5 min"), zarr_dataset)
