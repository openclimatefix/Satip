"""Script to run end-to-end and generate plots to verify correct processing.

This script generates end-to-end data prep and plots for making sure the data is being processed
correctly.
You will find the generated plots in the current working directory.

Usage example:
  python3 generate_test_plots.py
"""
import glob
import os
from pathlib import Path

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import rasterio
import xarray as xr

from satip import eumetsat
from satip.utils import (
    load_cloudmask_to_dataarray,
    load_native_to_dataarray,
    save_dataarray_to_zarr,
)


def generate_test_plots():
    """Function to generate test plots.

    Test plot generation code is encapsulated in a function to allow for easier testing.
    """
    RSS_ID = "EO:EUM:DAT:MSG:MSG15-RSS"
    CLOUD_ID = "EO:EUM:DAT:MSG:RSS-CLM"

    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")

    download_manager = eumetsat.DownloadManager(
        user_key=user_key,
        user_secret=user_secret,
        data_dir=os.getcwd(),
        logger_name="Plotting_test",
    )

    # Get 1 RSS native file and 1 cloud mask file
    download_manager.download_date_range(
        start_date="2020-06-01 11:59:00", end_date="2020-06-01 12:00:00", product_id=RSS_ID
    )

    # 1 Cloud mask
    download_manager.download_date_range(
        start_date="2020-06-01 11:59:00", end_date="2020-06-01 12:02:00", product_id=CLOUD_ID
    )

    # Store filenames just downloaded to later convert them to Xarray DataArray:
    rss_filenames = list(glob.glob(os.path.join(os.getcwd(), "*.nat")))
    cloud_mask_filenames = list(glob.glob(os.path.join(os.getcwd(), "*.grb")))

    def _plot_dataset(dataset: xr.DataArray, name: str, area: str) -> None:
        """Plots a xarray-dataset and saves the output to a defined filename.

        Args:
            dataset: xarray data set to plot.
            name: File base name to write to.
            area: Area suffix for the filename; get appended to `name`.
        """
        if area == "UK":
            ax = plt.axes(projection=ccrs.OSGB())
            dataset.plot.pcolormesh(
                ax=ax, transform=ccrs.OSGB(), x="x_osgb", y="y_osgb", add_colorbar=True,
            )
        else:
            ax = plt.axes(projection=ccrs.Geostationary(central_longitude=9.5))
            dataset.plot.pcolormesh(
                ax=ax,
                transform=ccrs.Geostationary(central_longitude=9.5),
                x="x_geostationary",
                y="y_geostationary",
                add_colorbar=True,
            )
        ax.coastlines()
        plt.savefig(os.path.join(os.getcwd(), f"{name}_{area}.png"))
        plt.cla()
        plt.clf()

    for area in ["UK", "RSS"]:
        # First do it with the cloud mask
        cloudmask_dataarray = load_cloudmask_to_dataarray(
            Path(cloud_mask_filenames[0]), temp_directory=Path(os.getcwd()), area=area
        )
        rss_dataarray, hrv_dataarray = load_native_to_dataarray(
            Path(rss_filenames[0]), temp_directory=Path(os.getcwd()), area=area
        )

        # Save to Zarrs, to then load them back
        save_dataarray_to_zarr(
            cloudmask_dataarray,
            zarr_path=os.path.join(os.getcwd(), "cloud.zarr"),
            compressor_name="bz2",
            zarr_mode="w",
        )
        del cloudmask_dataarray

        save_dataarray_to_zarr(
            rss_dataarray,
            zarr_path=os.path.join(os.getcwd(), "rss.zarr"),
            compressor_name="jpeg-xl",
            zarr_mode="w",
        )
        del rss_dataarray

        save_dataarray_to_zarr(
            hrv_dataarray,
            zarr_path=os.path.join(os.getcwd(), "hrv.zarr"),
            compressor_name="jpeg-xl",
            zarr_mode="w",
        )
        del hrv_dataarray

        # Load them from Zarr to ensure its the same as the output from satip
        cloudmask_dataarray = (
            xr.open_zarr(os.path.join(os.getcwd(), "cloud.zarr"), consolidated=True)["data"]
            .isel(time=0)
            .sel(variable="cloud_mask")
        )
        rss_dataarray = (
            xr.open_zarr(os.path.join(os.getcwd(), "rss.zarr"), consolidated=True)["data"]
            .isel(time=0)
            .sel(variable="IR_016")
        )
        hrv_dataarray = (
            xr.open_zarr(os.path.join(os.getcwd(), "hrv.zarr"), consolidated=True)["data"]
            .isel(time=0)
            .sel(variable="HRV")
        )

        print(cloudmask_dataarray)
        print(rss_dataarray)
        print(hrv_dataarray)

        _plot_dataset(hrv_dataarray, "hrv", area)
        _plot_dataset(rss_dataarray, "rss", area)
        _plot_dataset(cloudmask_dataarray, "cloud_mask", area)


if __name__ == "__main__":
    generate_test_plots()
