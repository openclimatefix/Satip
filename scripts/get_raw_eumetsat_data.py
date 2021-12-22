############
# Pull raw satellite data from EUMetSat
#
# 2021-09-28
# Jacob Bieker
#
############
from datetime import datetime

import click
import pandas as pd

import satip.download

NATIVE_FILESIZE_MB = 102.210123
CLOUD_FILESIZE_MB = 3.445185
RSS_ID = "EO:EUM:DAT:MSG:MSG15-RSS"
CLOUD_ID = "EO:EUM:DAT:MSG:RSS-CLM"

format_dt_str = lambda dt: pd.to_datetime(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_date(ctx, param, value):
    try:
        return format_dt_str(value)
    except ValueError:
        raise click.BadParameter("Date must be in format accepted by pd.to_datetime()")


@click.command()
@click.option(
    "--download_directory",
    "--dir",
    default="/storage/",
    help="Where to download the data to. Also where the script searches for previously downloaded data.",
)
@click.option(
    "--start_date",
    "--start",
    default="2010-01-01",
    prompt="Starting date to download data, in format accepted by pd.to_datetime()",
    callback=validate_date,
)
@click.option(
    "--end_date",
    "--end",
    default=datetime.now().strftime("%Y-%m-%d"),
    prompt="Ending date to download data, in format accepted by pd.to_datetime()",
    callback=validate_date,
)
@click.option(
    "--backfill",
    "-b",
    default=False,
    prompt="Whether to download any missing data from the start date of the data on disk to the end date",
    is_flag=True,
)
@click.option(
    "--user_key",
    "--key",
    default=None,
    help="The User Key for EUMETSAT access. Alternatively, the user key can be set using an auth file.",
)
@click.option(
    "--user_secret",
    "--secret",
    default=None,
    help="The User secret for EUMETSAT access. Alternatively, the user secret can be set using an auth file.",
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
    satip.download.download_eumetsat_data(*args, **kwargs)


if __name__ == "__main__":
    download_sat_files()
