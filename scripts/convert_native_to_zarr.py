"""Script to provide an annotated CLI for split_per_month."""
import click

from satip.intermediate import split_per_month


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
    "--hrv_zarr_path",
    "-hrv_zarr",
    default="hrv_eumetsat_zarr.zarr",
    prompt="The location for the HRV Zarr file",
)
@click.option(
    "--temp_directory", "-temp", default="/mnt/ramdisk/", prompt="Where to store temp directory",
)
@click.option(
    "--region",
    default="RSS",
    prompt="The name of the geographic region to use, default 'UK', use 'RSS' for full extant ",
)
def create_eumetsat_zarr(*args, **kwargs):
    """Wrapper around split_per_month to attach decorators to."""
    split_per_month(*args, **kwargs)


if __name__ == "__main__":
    create_eumetsat_zarr()
