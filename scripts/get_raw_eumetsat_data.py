""" Pull raw satellite data from EUMetSat

Wrapper to generate an annotated CLI around the downloader
and download the data.

Author(s): Jacob Bieker

Usage example:
  python3 get_raw_eumetsat_data.py
"""

import os
from datetime import datetime

import click

import satip.download.download
from satip.utils import format_dt_str

NATIVE_FILESIZE_MB = 102.210123
CLOUD_FILESIZE_MB = 3.445185
RSS_ID = "EO:EUM:DAT:MSG:MSG15-RSS"
CLOUD_ID = "EO:EUM:DAT:MSG:RSS-CLM"


def _validate_date(ctx, param, value):
    try:
        return format_dt_str(value)
    except ValueError:
        raise click.BadParameter("Date must be in format accepted by pd.to_datetime()")


@click.command()
@click.option(
    "--download_directory",
    "--dir",
    default=str(os.getcwd() + "/storage/"),
    prompt="""Where to download the data to and/or search for previously downloaded data.\n""",
)
@click.option(
    "--start_date",
    "--start",
    default="2010-01-01",
    prompt="Starting date to download data, in format accepted by pd.to_datetime()",
    callback=_validate_date,
)
@click.option(
    "--end_date",
    "--end",
    default=datetime.now().strftime("%Y-%m-%d"),
    prompt="Ending date to download data, in format accepted by pd.to_datetime()",
    callback=_validate_date,
)
@click.option(
    "--backfill",
    "-b",
    default=False,
    prompt="Whether to download missing data from the start date of data on disk to the end date",
    is_flag=True,
)
@click.option(
    "--user_key",
    "--key",
    default=None,
    help="""The User Key for EUMETSAT access.
            Alternatively, the user key can be set using an auth file.""",
)
@click.option(
    "--user_secret",
    "--secret",
    default=None,
    help="""The user secret for EUMETSAT access.
            Alternatively, the user secret can be set using an auth file.""",
)
@click.option(
    "--auth_filename",
    default=None,
    help="The auth file containing the user key and access key for EUMETSAT access",
)
@click.option(
    "--bandwidth_limit",
    "--bw_limit",
    default=0.0,
    prompt="Bandwidth limit, in MB/sec, currently ignored",
    type=float,
)
@click.option(
    "--number_of_processes",
    "--np",
    default=4,
    prompt="Number of processes to use",
    type=int,
)
@click.option(
    "--product",
    "--p",
    multiple=True,
    default=["rss", "cloud"],
    help="Which products to download, of 'rss' and 'cloud' ",
)
def download_sat_files(*args, **kwargs):
    """Wrapper around downloader for eumetsat data to attach decorators to it."""
    satip.download.download.download_eumetsat_data(*args, **kwargs)


if __name__ == "__main__":
    download_sat_files()
