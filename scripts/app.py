""" Application that pulls data from the EUMETSAT API and saves to a zarr file"""
import glob
import logging
import os

import click
import pandas as pd

from satip.eumetsat import DownloadManager
from satip.utils import save_native_to_netcdf

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s:%(message)s")
logging.getLogger("satip").setLevel(getattr(logging, os.environ.get("LOG_LEVEL", "INFO")))
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--api-key",
    default=None,
    envvar="API_KEY",
    help="The API key for EUMETSAT Data Center",
    type=click.STRING,
)
@click.option(
    "--api-secret",
    default=None,
    envvar="API_SECRET",
    help="The API secret for EUMETSAT Data Center",
    type=click.STRING,
)
@click.option(
    "--save-dir",
    default=None,
    envvar="SAVE_DIR",
    help="Where to save the zarr files",
    type=click.STRING,
)
@click.option(
    "--history",
    default="1 hour",
    envvar="HISTORY",
    help="How much history to save",
    type=click.STRING,
)
def run(api_key, api_secret, save_dir, history):
    """Run main application

    Args:
        api_key: API Key for EUMETSAT
        api_secret: Secret for EUMETSAT
        save_dir: Save directory
        history: History time
    """

    logger.info(f'Running application and saving to "{save_dir}"')
    # 1. Get data from API, download native files
    download_manager = DownloadManager(user_key=api_key, user_secret=api_secret, data_dir=save_dir)
    download_manager.download_date_range(
        start_date=(pd.Timestamp.now() - pd.Timedelta(history)).strftime("%Y-%m-%d-%H-%M-%S"),
        end_date=pd.Timestamp.now().strftime("%Y-%m-%d-%H-%M-%S"),
    )

    # 2. Load grib files to one Xarray Dataset
    native_files = list(glob.glob(os.path.join(save_dir, "*.nat")))
    # data = datahub.load_all_files()
    save_native_to_netcdf(native_files, save_dir=save_dir)

    logger.info("Finished Running application.")


if __name__ == "__main__":
    run()
