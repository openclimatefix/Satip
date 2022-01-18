import click

from satip.intermediate import create_or_update_zarr_with_native_files, split_per_month


@click.command()
@click.option(
    "--directory",
    "--dir",
    default="/run/media/jacob/data/EUMETSAT/",
    help="The top level directory where the native files are stored",
)
@click.option(
    "--zarr_path",
    "-zarr",
    default="/run/media/jacob/data/june2020_rss",
    prompt="The location for the non-HRV Zarr file",
)
@click.option(
    "--hrv_zarr_path",
    "-hrv_zarr",
    default="/run/media/jacob/data/june2020_rss_hrv",
    prompt="The location for the HRV Zarr file",
)
@click.option(
    "--temp_directory",
    "-temp",
    default="/run/media/jacob/data/",
    prompt="Where to store temp directory",
)
@click.option(
    "--region",
    default="RSS",
    prompt="The name of the geographic region to use, default 'UK', use 'RSS' for full extant ",
)
def create_eumetsat_zarr(*args, **kwargs):
    split_per_month(*args, **kwargs)


if __name__ == "__main__":
    create_eumetsat_zarr()
