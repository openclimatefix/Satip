"""
This script generates end 2 end data prep and plots for making sure the data is being processed
correctly.
"""
import glob
import os
from pathlib import Path

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import rasterio
import xarray as xr

from satip import eumetsat
from satip.utils import load_cloudmask_to_dataset, load_native_to_dataset, save_dataset_to_zarr

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


def plot_tailored(input_name: str) -> None:
    geotiff_files = list(glob.glob(os.path.join(os.getcwd(), "*.tif")))
    image = rasterio.open(geotiff_files[0])
    plt.imshow(image.read(1))
    plt.title(f"Tailored {input_name}")
    plt.savefig(os.path.join(os.getcwd(), f"tailored_{input_name}.png"), dpi=300)
    plt.cla()
    plt.clf()
    os.remove(geotiff_files[0])


# Then tailored ones
download_manager.download_tailored_date_range(
    start_date="2020-06-01 11:59:00",
    end_date="2020-06-01 12:02:00",
    file_format="geotiff",
    product_id=CLOUD_ID,
)
plot_tailored("cloud_mask")
download_manager.download_tailored_date_range(
    start_date="2020-06-01 11:59:00",
    end_date="2020-06-01 12:00:00",
    file_format="geotiff",
    product_id=RSS_ID,
)
plot_tailored("rss")

# Get 1 RSS native file and 1 cloud mask file
download_manager.download_date_range(
    start_date="2020-06-01 11:59:00", end_date="2020-06-01 12:00:00", product_id=RSS_ID
)
# 1 Cloud mask
download_manager.download_date_range(
    start_date="2020-06-01 11:59:00", end_date="2020-06-01 12:02:00", product_id=CLOUD_ID
)

# Convert to Xarray DataArray
rss_filename = list(glob.glob(os.path.join(os.getcwd(), "*.nat")))
cloud_mask_filename = list(glob.glob(os.path.join(os.getcwd(), "*.grb")))


def plot_dataset(dataset: xr.DataArray, name: str, area: str) -> None:
    ax = plt.axes(projection=ccrs.OSGB())
    dataset.plot.pcolormesh(
        ax=ax,
        transform=ccrs.OSGB(),
        x="x_osgb",
        y="y_osgb",
        add_colorbar=True,
    )
    ax.coastlines()
    plt.savefig(os.path.join(os.getcwd(), f"{name}_{area}.png"))
    plt.cla()
    plt.clf()


for area in [
    "UK",
]:
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
    cloudmask_dataset = (
        xr.open_zarr(os.path.join(os.getcwd(), "cloud.zarr"), consolidated=True)[
            "stacked_eumetsat_data"
        ]
        .isel(time=0)
        .sel(variable="cloud_mask")
    )
    rss_dataset = (
        xr.open_zarr(os.path.join(os.getcwd(), "rss.zarr"), consolidated=True)[
            "stacked_eumetsat_data"
        ]
        .isel(time=0)
        .sel(variable="IR_016")
    )
    hrv_dataset = (
        xr.open_zarr(os.path.join(os.getcwd(), "hrv.zarr"), consolidated=True)[
            "stacked_eumetsat_data"
        ]
        .isel(time=0)
        .sel(variable="HRV")
    )

    print(cloudmask_dataset)
    print(rss_dataset)
    print(hrv_dataset)

    plot_dataset(hrv_dataset, "hrv", area)
    plot_dataset(rss_dataset, "rss", area)
    plot_dataset(cloudmask_dataset, "cloud_mask", area)
