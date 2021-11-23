import click

from satip.intermediate import create_or_update_zarr_with_native_files, split_per_month


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
    "--temp_directory",
    "-temp",
    default="/mnt/ramdisk/",
    prompt="Where to store temp directory",
)
@click.option(
    "--region",
    default="UK",
    prompt="The name of the geographic region to use, default 'UK' ",
)
def create_eumetsat_zarr(*args, **kwargs):
    split_per_month(*args, **kwargs)


if __name__ == "__main__":
    create_eumetsat_zarr()
