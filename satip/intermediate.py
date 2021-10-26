from satip.utils import (
    load_native_to_dataset,
    save_dataset_to_zarr,
    check_if_timestep_exists,
    round_datetime_to_nearest_5_minutes,
)
from satip.eumetsat import eumetsat_filename_to_datetime, eumetsat_cloud_name_to_datetime
import os
import fsspec
from pathlib import Path
import multiprocessing
from itertools import repeat
import xarray as xr


def create_or_update_zarr_with_native_files(
    directory: str, zarr_path: str, spatial_chunk_size: int = 256, temporal_chunk_size: int = 1
) -> None:
    """
    Creates or updates a zarr file with satellite native files

    Args:
        directory: Top-level directory containing the compressed native files
        zarr_path: Path of the final Zarr file

    Returns:

    """

    # Satpy Scene doesn't do well with fsspec
    compressed_native_files = list(Path(directory).rglob("*.bz2"))
    number_of_timesteps = len(compressed_native_files)
    print(number_of_timesteps)
    zarr_exists = os.path.exists(zarr_path)
    if zarr_exists:
        zarr_dataset = xr.open_zarr(zarr_path, consolidated=True)
        print(zarr_dataset)
        new_compressed_files = []
        for f in compressed_native_files:
            base_filename = f.name
            file_timestep = eumetsat_filename_to_datetime(str(base_filename))
            exists = check_if_timestep_exists(
                round_datetime_to_nearest_5_minutes(file_timestep), zarr_dataset
            )
            if not exists:
                new_compressed_files.append(f)
        compressed_native_files = new_compressed_files
        print(len(new_compressed_files))
    pool = multiprocessing.Pool(processes=4)
    # Check if zarr already exists
    if not zarr_exists:
        # Inital zarr path before then appending
        dataset = load_native_to_dataset(
            [compressed_native_files[0], "/home/jacob/Development/Satip/tests"]
        )

        save_dataset_to_zarr(dataset, zarr_filename=zarr_path, zarr_mode="w")
    for dataset in pool.imap_unordered(
        load_native_to_dataset,
        zip(
            compressed_native_files[1:] if not zarr_exists else compressed_native_files,
            repeat("/home/jacob/Development/Satip/tests"),
        ),
    ):
        save_dataset_to_zarr(
            dataset,
            zarr_filename=zarr_path,
            x_size_per_chunk=spatial_chunk_size,
            y_size_per_chunk=spatial_chunk_size,
            timesteps_per_chunk=temporal_chunk_size,
        )
        del dataset


create_or_update_zarr_with_native_files("/home/jacob/Development/Satip", "zarr_test.zarr")
