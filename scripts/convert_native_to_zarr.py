from satip.intermediate import create_or_update_zarr_with_native_files
import click


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
    prompt="The location for the Zarr file",
)
@click.option(
    "--region",
    default="UK",
    prompt="The name of the geographic region to use, default 'UK' ",
)
def create_eumetsat_zarr(*args, **kwargs):
    create_or_update_zarr_with_native_files(*args, **kwargs)


if __name__ == "__main__":
    create_eumetsat_zarr()
