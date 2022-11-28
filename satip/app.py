""" Application that pulls data from the EUMETSAT API and saves to a zarr file"""
import datetime
import glob
import logging
import os
import tempfile
from typing import Optional

import click
import pandas as pd
import psutil
from nowcasting_datamodel.connection import DatabaseConnection
from nowcasting_datamodel.models.base import Base_Forecast
from nowcasting_datamodel.read.read import update_latest_input_data_last_updated

from satip.eumetsat import DownloadManager
from satip.utils import (
    collate_files_into_latest,
    filter_dataset_ids_on_current_files,
    move_older_files_to_different_location,
    save_native_to_zarr,
)

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s:%(message)s")
logging.getLogger("satip").setLevel(getattr(logging, os.environ.get("LOG_LEVEL", "INFO")))
logger = logging.getLogger(__name__)
logging.getLogger(__name__).setLevel(logging.INFO)


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
    default="./",
    envvar="SAVE_DIR",
    help="Where to save the zarr files",
    type=click.STRING,
)
@click.option(
    "--history",
    default="60 minutes",
    envvar="HISTORY",
    help="How much history to save",
    type=click.STRING,
)
@click.option(
    "--db-url",
    default=None,
    envvar="DB_URL",
    help="Database to save when this has run",
    type=click.STRING,
)
@click.option(
    "--use-rescaler",
    default=False,
    envvar="USE_RESCALER",
    help="Whether to rescale data to between 0 and 1 or not",
    type=click.BOOL,
)
@click.option(
    "--start-time",
    envvar="START_TIME",
    default=pd.Timestamp.utcnow().isoformat(timespec="minutes").split("+")[0],
    help="Start time, defaults to the current UTC time",
    type=click.STRING,
)
def run(
    api_key,
    api_secret,
    save_dir,
    history,
    db_url: Optional[str] = None,
    use_rescaler: bool = False,
    start_time: str = pd.Timestamp.utcnow().isoformat(timespec="minutes").split("+")[0],
):
    """Run main application

    Args:
        api_key: API Key for EUMETSAT
        api_secret: Secret for EUMETSAT
        save_dir: Save directory
        history: History time
        db_url: URL of database
        use_rescaler: Rescale data to between 0 and 1 or not
        start_time: Start time in UTC ISO Format
    """

    logger.info(f'Running application and saving to "{save_dir}"')
    using_backup = False
    # 1. Get data from API, download native files
    with tempfile.TemporaryDirectory() as tmpdir:
        download_manager = DownloadManager(
            user_key=api_key, user_secret=api_secret, data_dir=tmpdir
        )
        start_date = pd.Timestamp(start_time, tz="UTC") - pd.Timedelta(history)
        logger.info(start_date)
        logger.info(start_time)
        datasets = download_manager.identify_available_datasets(
            start_date=start_date.strftime("%Y-%m-%d-%H-%M-%S"),
            end_date=pd.Timestamp(start_time, tz="UTC").strftime("%Y-%m-%d-%H-%M-%S"),
        )
        logger.info(
            f"Memory in use: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2} MB"
        )
        logger.info(
            f"Memory in use: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2} MB"
        )
        # Check if any RSS imagery is available, if not, fall back to 15 minutely data
        if len(datasets) == 0:
            logger.info("No RSS Imagery available, falling back to 15-minutely data")
            datasets = download_manager.identify_available_datasets(
                start_date=start_date.strftime("%Y-%m-%d-%H-%M-%S"),
                end_date=pd.Timestamp(start_time, tz="UTC").strftime("%Y-%m-%d-%H-%M-%S"),
                product_id="EO:EUM:DAT:MSG:HRSEVIRI",
            )
            using_backup = True
        # Filter out ones that already exist
        logger.info(
            f"Memory in use: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2} MB"
        )
        datasets = filter_dataset_ids_on_current_files(datasets, save_dir)
        logger.info(f"Files to download after filtering: {len(datasets)}")

        if len(datasets) == 0:
            logger.info("No files to download, exiting")
            return
        if using_backup:

            download_manager.download_tailored_datasets(
                datasets,
                product_id="EO:EUM:DAT:MSG:HRSEVIRI",
            )
        else:
            download_manager.download_datasets(
                datasets,
                product_id="EO:EUM:DAT:MSG:MSG15-RSS",
            )
        logger.info(
            f"Memory in use: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2} MB"
        )

        # 2. Load nat files to one Xarray Dataset
        native_files = (
            list(glob.glob(os.path.join(tmpdir, "*.nat")))
            if not using_backup
            else list(glob.glob(os.path.join(tmpdir, "*HRSEVIRI*")))
        )
        logger.info(native_files)
        # Save to S3
        save_native_to_zarr(
            native_files, save_dir=save_dir, use_rescaler=use_rescaler, using_backup=using_backup
        )
        logger.info(
            f"Memory in use: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2} MB"
        )

        # Move around files into and out of latest
        move_older_files_to_different_location(
            save_dir=save_dir, history_time=(start_date - pd.Timedelta("30 min"))
        )
        logger.info(
            f"Memory in use: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2} MB"
        )

        # Collate files into single NetCDF file
        collate_files_into_latest(save_dir=save_dir, using_backup=using_backup)
        logger.info(
            f"Memory in use: {psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2} MB"
        )

    # 4. update table to show when this data has been pulled
    if db_url is not None:
        connection = DatabaseConnection(url=db_url, base=Base_Forecast)
        with connection.get_session() as session:
            update_latest_input_data_last_updated(session=session, component="satellite")

    logger.info("Finished Running application.")


if __name__ == "__main__":
    run()
