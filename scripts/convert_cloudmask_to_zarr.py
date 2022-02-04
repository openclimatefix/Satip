"""Script to provide an annotated CLI for cloudmask_split_per_month."""
import click

from satip.intermediate import cloudmask_split_per_month


@click.command()
@click.option(
    "--directory",
    "--dir",
    default="/storage/",
    help="The top level directory where the native files are stored",
)
@click.option(
    "--zarr_path",
    "-zarr",
    default="eumetsat_zarr.zarr",
    prompt="The location for the non-HRV Zarr file",
)
@click.option(
    "--temp_directory",
    "-temp",
    default="/mnt/ramdisk/",
    prompt="Where to store temp directory",
)
@click.option(
    "--region",
    default="UK",
    prompt="The name of the geographic region to use, default 'UK', use 'RSS' for whole extant ",
)
def create_eumetsat_zarr(*args, **kwargs):
    """Wrapper around cloudmask_split_per_month to attach decorators to."""
    cloudmask_split_per_month(*args, **kwargs)


if __name__ == "__main__":
    create_eumetsat_zarr()
