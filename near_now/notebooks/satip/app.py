""" Application that pulls data from the EUMETSAT API and saves to a zarr file

We now support
- The 0 deg HR-SERVIRI data - https://masif.eumetsat.int/ossi/webpages/level3.html?ossi_level3_filename=seviri_0deg_hr.html&ossi_level2_filename=seviri_0deg.html
- The 9.5 deg RSS data - https://masif.eumetsat.int/ossi/webpages/level2.html?ossi_level2_filename=seviri_rss.html
- The 45.5 deg IODC data - https://masif.eumetsat.int/ossi/webpages/level2.html?ossi_level2_filename=seviri_iodc.html

By-default we pull the RSS data, if not available we try the HR-SERVIRI.
We have an option to just use the IODC data.
"""
import glob
import os
import random
import tempfile
from typing import Optional

import click
import pandas as pd
import sentry_sdk
import structlog

import satip
from satip import utils
from satip.constants import RSS_ID, SEVIRI_ID, SEVIRI_IODC_ID
from satip.eumetsat import EUMETSATDownloadManager

log = structlog.stdlib.get_logger()
#sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "local"),
    traces_sample_rate=1
)
sentry_sdk.set_tag("app_name", "satellite_consumer")
sentry_sdk.set_tag("version", satip.__version__)

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
    "--use-hr-serviri",
    envvar="USE_HR_SERVIRI",
    default=False,
    help="Option not to use the RSS imaginary. If True, use the 15 mins data. ",
    type=click.BOOL,
)
@click.option(
    "--maximum-n-datasets",
    envvar="MAXIMUM_N_DATASETS",
    default=-1,
    help="Set the maximum number of dataset to load, default gets them all",
    type=click.INT,
)
@click.option(
    "--use-iodc",
    envvar="USE_IODC",
    default=False,
    help="An option to use the IODC data instead of the RSS data.",
    type=click.BOOL,
)
def run_click(
    api_key,
    api_secret,
    save_dir,
    save_dir_native,
    history,
    db_url: Optional[str] = None,
    use_rescaler: bool = False,
    start_time: str = pd.Timestamp.utcnow().isoformat(timespec="minutes").split("+")[0],
    cleanup: bool = False,
    use_hr_serviri: bool = False,
    maximum_n_datasets: int = -1,
    use_iodc: bool = False,
):
    """ See below for function description.

    There is slight duplicate, but testing and debugging is easier with this setup.
    """
    run(
        api_key,
        api_secret,
        save_dir,
        save_dir_native,
        history,
        use_rescaler=use_rescaler,
        start_time=start_time,
        cleanup=cleanup,
        use_hr_serviri=use_hr_serviri,
        maximum_n_datasets=maximum_n_datasets,
        use_iodc=use_iodc
    )



def run(
    api_key,
    api_secret,
    save_dir = './',
    save_dir_native = "./raw",
    history="60 minutes",
    use_rescaler: bool = False,
    start_time: str = pd.Timestamp.utcnow().isoformat(timespec="minutes").split("+")[0],
    cleanup: bool = False,
    use_hr_serviri: bool = False,
    maximum_n_datasets: int = -1,
    use_iodc: bool = False,
):
    """Run main application

    Args:
        api_key: API Key for EUMETSAT
        api_secret: Secret for EUMETSAT
        save_dir: Save directory
        save_dir_native: where the native files are saved
        history: History time
        use_rescaler: Rescale data to between 0 and 1 or not
        start_time: Start time in UTC ISO Format
        cleanup: Cleanup Data Tailor
        use_hr_serviri: use 15 min data, not RSS
        maximum_n_datasets: Set the maximum number of dataset to load, default gets them all
        use_iodc: Use IODC data instead
    """

    utils.setupLogging()

    try:
        if save_dir != "./":
            log.info("Checking if save_dir directory exists")
            if utils.check_path_is_exists_and_directory(save_dir):
                log.info("save_dir directory exists, continuing execution")

        # dont check if save_dir_native exists, as it is created by the download manager
        # and only used if the data tailor service is used

        log.info(
            f'Running application and saving to "{save_dir}"',
            version=satip.__version__,
            memory=utils.get_memory(),
        )
        # 1. Get data from API, download native files
        with tempfile.TemporaryDirectory() as tmpdir:

            start_date = pd.Timestamp(start_time, tz="UTC") - pd.Timedelta(history)
            log.info(
                f"Fetching datasets for {start_date} - {start_time}", memory=utils.get_memory()
            )

            if use_iodc:
                # get the IODC data
                log.info(
                    f"Fetching IODC datasets for {start_date} - {start_time}",
                    memory=utils.get_memory(),
                )
                download_manager = EUMETSATDownloadManager(
                    user_key=api_key,
                    user_secret=api_secret,
                    data_dir=tmpdir,
                    native_file_dir=save_dir_native,
                )
                datasets = download_manager.identify_available_datasets(
                    start_date=start_date.strftime("%Y-%m-%d-%H:%M:%S"),
                    end_date=pd.Timestamp(start_time, tz="UTC").strftime("%Y-%m-%d-%H:%M:%S"),
                    product_id=SEVIRI_IODC_ID,
                )

            else:
                # try rss, then get hr_serviri data if not rss
                download_manager = EUMETSATDownloadManager(
                    user_key=api_key,
                    user_secret=api_secret,
                    data_dir=tmpdir,
                    native_file_dir=save_dir_native,
                )
                if cleanup:
                    log.debug("Running Data Tailor Cleanup", memory=utils.get_memory())
                    download_manager.cleanup_datatailor()
                    return

                datasets = download_manager.identify_available_datasets(
                    start_date=start_date.strftime("%Y-%m-%d-%H:%M:%S"),
                    end_date=pd.Timestamp(start_time, tz="UTC").strftime("%Y-%m-%d-%H:%M:%S"),
                )

                # Check if any RSS imagery is available, if not, fall back to 15 minutely data
                # We want to check if there is at least 75% of the history data available
                # If there is less than this, we move over to the 15 minute data
                # note we need history data to be larger than this.
                n_datasets_needed = int(pd.to_timedelta(history) / pd.Timedelta("5 min") * 0.75)
                if (len(datasets) < n_datasets_needed) or use_hr_serviri:
                    log.warn(
                        f"No RSS Imagery available or using backup ({use_hr_serviri=}), "
                        f"falling back to 15-minutely data",
                        memory=utils.get_memory(),
                    )
                    datasets = download_manager.identify_available_datasets(
                        start_date=start_date.strftime("%Y-%m-%d-%H:%M:%S"),
                        end_date=pd.Timestamp(start_time, tz="UTC").strftime("%Y-%m-%d-%H:%M:%S"),
                        product_id=SEVIRI_ID,
                    )
                    use_hr_serviri = True

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
                random.shuffle(datasets)  # Shuffle so subsequent runs might download different data
                updated_data = True
                if use_hr_serviri:
                    # Check before downloading each tailored dataset, as it can take awhile
                    for dset in datasets:
                        dset = utils.filter_dataset_ids_on_current_files([dset], save_dir)
                        if len(dset) > 0:
                            download_manager.download_tailored_datasets(
                                dset,
                                product_id=SEVIRI_ID,
                            )
                elif use_iodc:
                    # Check before downloading each dataset, as it can take a while
                    for dset in datasets:
                        dset = utils.filter_dataset_ids_on_current_files([dset], save_dir)
                        if len(dset) > 0:
                            # note we might have to change this to the data taylor
                            download_manager.download_datasets(
                                dset,
                                product_id=SEVIRI_IODC_ID,
                            )

                else:
                    # Check before downloading each tailored dataset, as it can take awhile
                    for dset in datasets:
                        dset = utils.filter_dataset_ids_on_current_files([dset], save_dir)
                        if len(dset) > 0:
                            download_manager.download_datasets(
                                dset,
                                product_id=RSS_ID,
                            )

                # 2. Load nat files to one Xarray Dataset
                if use_hr_serviri:
                    native_files = list(glob.glob(os.path.join(tmpdir, "*HRSEVIRI*")))
                else:
                    # RSS or IODC
                    native_files = list(glob.glob(os.path.join(tmpdir, "*.nat")))

                log.debug(
                    "Saving native files to Zarr: " + native_files.__str__(),
                    memory=utils.get_memory(),
                )
                # Save to S3
                utils.save_native_to_zarr(
                    native_files,
                    save_dir=save_dir,
                    use_rescaler=use_rescaler,
                    use_hr_serviri=use_hr_serviri,
                    use_iodc=use_iodc,
                )
                # Move around files into and out of latest
                utils.move_older_files_to_different_location(
                    save_dir=save_dir, history_time=(start_date - pd.Timedelta("30 min"))
                )

        if not utils.check_both_final_files_exists(save_dir=save_dir,
                                                   use_hr_serviri=use_hr_serviri,
                                                   use_iodc=use_iodc):
            updated_data = True

        if updated_data:
            # Collate files into single NetCDF file
            utils.collate_files_into_latest(save_dir=save_dir,
                                            use_hr_serviri=use_hr_serviri,
                                            use_iodc=use_iodc)
            log.debug("Collated files", memory=utils.get_memory())

        log.info("Finished Running application", memory=utils.get_memory())

    except Exception as e:
        log.error(f"Error caught during run: {e}", exc_info=True)
        raise e


if __name__ == "__main__":
    run_click()
