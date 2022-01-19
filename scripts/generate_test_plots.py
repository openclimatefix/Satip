"""
This script generates end 2 end data prep and plots for making sure the data is being processed
correctly.
"""
import satip
from satip import eumetsat
from satip import download
from satip import intermediate
from satip.utils import (
    check_if_timestep_exists,
    load_cloudmask_to_dataset,
    load_native_to_dataset,
    save_dataset_to_zarr,
    )
import os
import glob
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from satpy import Scene
from pathlib import Path

RSS_ID = "EO:EUM:DAT:MSG:MSG15-RSS"
CLOUD_ID = "EO:EUM:DAT:MSG:RSS-CLM"

user_key = os.environ.get("EUMETSAT_USER_KEY")
user_secret = os.environ.get("EUMETSAT_USER_SECRET")

download_manager = eumetsat.DownloadManager(user_key = user_key, user_secret = user_secret, data_dir = os.getcwd(), log_fp = os.path.join(os.getcwd(), "log.txt"), logger_name = "Plotting_test")

# Get 1 RSS native file and 1 cloud mask file
download_manager.download_date_range(start_date = "2020-06-01 11:58:00", end_date = "2020-06-01 12:03:00", product_id = RSS_ID)
# 1 Cloud mask
download_manager.download_date_range(start_date = "2020-06-01 11:58:00", end_date = "2020-06-01 12:03:00", product_id = CLOUD_ID)

# Convert to Xarray DataArray
rss_filename = list(glob.glob(os.path.join(os.getcwd(), "*.nat")))
cloud_mask_filename = list(glob.glob(os.path.join(os.getcwd(), "*.grib")))
print(rss_filename)
print(cloud_mask_filename)

# First do it with the cloud mask
cloudmask_dataset = load_cloudmask_to_dataset(Path(cloud_mask_filename[0]), temp_directory = Path(os.getcwd()), area = 'RSS')
rss_dataset, hrv_dataset = load_native_to_dataset(Path(rss_filename[0]), temp_directory = Path(os.getcwd()), area='RSS')

# Convert scenes to data
# Then with the HRV RSS image

# Then with non-HRV RSS Image

# Then tailored cloud mask

# Then tailored HRV Image

# Then tailored non-HRV Image

