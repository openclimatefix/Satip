"""
This script generates end 2 end data prep and plots for making sure the data is being processed
correctly.
"""
import glob
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from satpy import Scene

import satip
from satip import download, eumetsat, intermediate
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

download_manager = eumetsat.DownloadManager(
    user_key=user_key,
    user_secret=user_secret,
    data_dir=os.getcwd(),
    log_fp=os.path.join(os.getcwd(), "log.txt"),
    logger_name="Plotting_test",
)

# Get 1 RSS native file and 1 cloud mask file
download_manager.download_date_range(
    start_date="2020-06-01 11:58:00", end_date="2020-06-01 12:03:00", product_id=RSS_ID
)
# 1 Cloud mask
download_manager.download_date_range(
    start_date="2020-06-01 11:58:00", end_date="2020-06-01 12:03:00", product_id=CLOUD_ID
)

# Convert to Xarray DataArray
rss_filename = list(glob.glob(os.path.join(os.getcwd(), "*.nat")))
cloud_mask_filename = list(glob.glob(os.path.join(os.getcwd(), "*.grib")))
print(rss_filename)
print(cloud_mask_filename)

for area in ['UK', 'RSS']:
    # First do it with the cloud mask
    cloudmask_dataset = load_cloudmask_to_dataset(
        Path(cloud_mask_filename[0]), temp_directory=Path(os.getcwd()), area=area
    )
    rss_dataset, hrv_dataset = load_native_to_dataset(
        Path(rss_filename[0]), temp_directory=Path(os.getcwd()), area=area
    )

    # Save to Zarrs, to then load them back
    save_dataset_to_zarr(
        cloudmask_dataset,
        zarr_path=os.path.join(os.getcwd(), "cloud.zarr"),
        channel_chunk_size=1,
        dtype="int8",
        zarr_mode="w",
        )
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

    # Load them from Zarr to ensure its the same as the output from satip
    cloudmask_dataset = xr.open_zarr(os.path.join(os.getcwd(), "cloud.zarr"), consolidated = True)
    rss_dataset = xr.open_zarr(os.path.join(os.getcwd(), "rss.zarr"), consolidated = True)
    hrv_dataset = xr.open_zarr(os.path.join(os.getcwd(), "hrv.zarr"), consolidated = True)



# Then tailored cloud mask

# Then tailored HRV Image

# Then tailored non-HRV Image
