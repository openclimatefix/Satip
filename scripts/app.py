""" Application that pulls data from the Metoffice API and saves to a zarr file"""
import logging
import os

import click

from satip.multiple_files import MetOfficeDataHub, save

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s:%(message)s")
logging.getLogger("metofficedatahub").setLevel(
    getattr(logging, os.environ.get("LOG_LEVEL", "INFO"))
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--api-key",
    default=None,
    envvar="API_KEY",
    help="The API key for MetOffice Weather DataHub",
    type=click.STRING,
)
@click.option(
    "--api-secret",
    default=None,
    envvar="API_SECRET",
    help="The API secret for MetOffice Weather DataHub",
    type=click.STRING,
)
@click.option(
    "--save-dir",
    default=None,
    envvar="SAVE_DIR",
    help="Where to save the zarr files",
    type=click.STRING,
)
def run(api_key, api_secret, save_dir):
    """Run main application
    1. Get data from API, download grip files
    2. Load grib files to one Xarray Dataset
    3. Save to directory
    """

    logger.info(f'Running application and saving to "{save_dir}"')
    # 1. Get data from API, download grip files
    datahub = MetOfficeDataHub(client_id=api_key, client_secret=api_secret)
    datahub.download_all_files()

    # 2. Load grib files to one Xarray Dataset
    data = datahub.load_all_files()

    # 3. Save to directory
    save(dataset=data, save_dir=save_dir)

    logger.info("Finished Running application.")


if __name__ == "__main__":
    run()
