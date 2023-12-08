""" Application that pulls data from the EUMETSAT API and saves to a zarr file"""
import glob
import os
import random
import tempfile
from typing import Optional

import click
import pandas as pd
import structlog
from nowcasting_datamodel.connection import DatabaseConnection
from nowcasting_datamodel.models.base import Base_Forecast
from nowcasting_datamodel.read.read import update_latest_input_data_last_updated

import satip
from satip import utils
from satip.eumetsat import DownloadManager

log = structlog.stdlib.get_logger()


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
    "--save-dir-native",
    default="./raw",
    envvar="SAVE_DIR_NATIVE",
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
@click.option(
    "--cleanup",
    envvar="CLEANUP",
    default=False,
    help="Run Data Tailor Cleanup and exit",
    type=click.BOOL,
)
@click.option(
    "--use-backup",
    envvar="USE_BACKUP",
    default=False,
    help="Option not to sue the RSS imaginary. If True, use the 15 mins data. ",
    type=click.BOOL,
)
@click.option(
    "--maximum-n-datasets",
    envvar="MAXIMUM_N_DATASETS",
    default=-1,
    help="Set the maximum number of dataset to load, default gets them all",
    type=click.INT,
)
def run(
    api_key,
    api_secret,
    save_dir,
    save_dir_native,
    history,
    db_url: Optional[str] = None,
    use_rescaler: bool = False,
    start_time: str = pd.Timestamp.utcnow().isoformat(timespec="minutes").split("+")[0],
    cleanup: bool = False,
    use_backup: bool = False,
    maximum_n_datasets: int = -1,
):
    """Run main application

    Args:
        api_key: API Key for EUMETSAT
        api_secret: Secret for EUMETSAT
        save_dir: Save directory
        save_dir_native: where the native files are saved
        history: History time
        db_url: URL of database
        use_rescaler: Rescale data to between 0 and 1 or not
        start_time: Start time in UTC ISO Format
        cleanup: Cleanup Data Tailor
        use_backup: use 15 min data, not RSS
        maximum_n_datasets: Set the maximum number of dataset to load, default gets them all
    """

    utils.setupLogging()

    try:

        log.info(
            f'Running application and saving to "{save_dir}"',
            version=satip.__version__,
            memory=utils.get_memory(),
        )
        # 1. Get data from API, download native files
        with tempfile.TemporaryDirectory() as tmpdir:
            download_manager = DownloadManager(
                user_key=api_key,
                user_secret=api_secret,
                data_dir=tmpdir,
                native_file_dir=save_dir_native,
            )
            if cleanup:
                log.debug("Running Data Tailor Cleanup", memory=utils.get_memory())
                download_manager.cleanup_datatailor()
                return
            start_date = pd.Timestamp(start_time, tz="UTC") - pd.Timedelta(history)
            log.info(f"Fetching datasets for {start_date} - {start_time}",
                     memory=utils.get_memory())
            datasets = download_manager.identify_available_datasets(
                start_date=start_date.strftime("%Y-%m-%d-%H:%M:%S"),
                end_date=pd.Timestamp(start_time, tz="UTC").strftime("%Y-%m-%d-%H:%M:%S"),
            )
            # Check if any RSS imagery is available, if not, fall back to 15 minutely data
            if (len(datasets) == 0) or use_backup:
                log.warn(
                    f"No RSS Imagery available or using backup ({use_backup=}), "
                    f"falling back to 15-minutely data",
                    memory=utils.get_memory(),
                )
                datasets = download_manager.identify_available_datasets(
                    start_date=start_date.strftime("%Y-%m-%d-%H:%M:%S"),
                    end_date=pd.Timestamp(start_time, tz="UTC").strftime("%Y-%m-%d-%H:%M:%S"),
                    product_id="EO:EUM:DAT:MSG:HRSEVIRI",
                )
                use_backup = True
            # Filter out ones that already exist
            # if both final files don't exist, then we should make sure we run the whole process
            datasets = utils.filter_dataset_ids_on_current_files(datasets, save_dir)
            log.info(
                f"Files to download after filtering: {len(datasets)}", memory=utils.get_memory()
            )

            if len(datasets) == 0:
                log.info("No files to download, exiting", memory=utils.get_memory())
                updated_data = False
            else:
                if maximum_n_datasets != -1:
                    log.debug(
                        f"Ony going to get at most {maximum_n_datasets} datasets",
                        memory=utils.get_memory(),
                    )
                    datasets = datasets[0:maximum_n_datasets]
                random.shuffle(datasets) # Shuffle so subsequent runs might download different data
                updated_data = True
                if use_backup:
                    # Check before downloading each tailored dataset, as it can take awhile
                    for dset in datasets:
                        dset = utils.filter_dataset_ids_on_current_files([dset], save_dir)
                        if len(dset) > 0:
                            download_manager.download_tailored_datasets(
                                dset,
                                product_id="EO:EUM:DAT:MSG:HRSEVIRI",
                            )
                else:
                    # Check before downloading each tailored dataset, as it can take awhile
                    for dset in datasets:
                        dset = utils.filter_dataset_ids_on_current_files([dset], save_dir)
                        if len(dset) > 0:
                            download_manager.download_datasets(
                                dset,
                                product_id="EO:EUM:DAT:MSG:MSG15-RSS",
                            )

                # 2. Load nat files to one Xarray Dataset
                native_files = (
                    list(glob.glob(os.path.join(tmpdir, "*.nat")))
                    if not use_backup
                    else list(glob.glob(os.path.join(tmpdir, "*HRSEVIRI*")))
                )
                log.debug(
                    "Saving native files to Zarr: " + native_files.__str__(),
                    memory=utils.get_memory(),
                )
                # Save to S3
                utils.save_native_to_zarr(
                    native_files,
                    save_dir=save_dir,
                    use_rescaler=use_rescaler,
                    using_backup=use_backup,
                )
                # Move around files into and out of latest
                utils.move_older_files_to_different_location(
                    save_dir=save_dir, history_time=(start_date - pd.Timedelta("30 min"))
                )

        if not utils.check_both_final_files_exists(save_dir=save_dir, using_backup=use_backup):
            updated_data = True

        if updated_data:
            # Collate files into single NetCDF file
            utils.collate_files_into_latest(save_dir=save_dir, using_backup=use_backup)
            log.debug("Collated files", memory=utils.get_memory())

            # 4. update table to show when this data has been pulled
            if db_url is not None:
                connection = DatabaseConnection(url=db_url, base=Base_Forecast)
                with connection.get_session() as session:
                    update_latest_input_data_last_updated(session=session, component="satellite")

        log.info("Finished Running application", memory=utils.get_memory())

    except Exception as e:
        log.error(f"Error caught during run: {e}", exc_info=True)
        raise e


if __name__ == "__main__":
    run()
