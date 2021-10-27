from satip.utils import (
    load_native_to_dataset,
    save_dataset_to_zarr,
    check_if_timestep_exists,
)
from satip.eumetsat import eumetsat_filename_to_datetime, eumetsat_cloud_name_to_datetime
import os
import pandas as pd
from pathlib import Path
import multiprocessing
from itertools import repeat
import xarray as xr


def create_or_update_zarr_with_native_files(
    directory: str,
    zarr_path: str,
    region: str,
    spatial_chunk_size: int = 256,
    temporal_chunk_size: int = 1,
) -> None:
    """
    Creates or updates a zarr file with satellite native files

    Args:
        directory: Top-level directory containing the compressed native files
        zarr_path: Path of the final Zarr file
        region: Name of the region to keep for the datastore
        spatial_chunk_size: Chunk size, in pixels in the x  and y directions, passed to Xarray
        temporal_chunk_size: Chunk size, in timesteps, for saving into the zarr file

    """

    # Satpy Scene doesn't do well with fsspec
    compressed_native_files = list(Path(directory).rglob("*.bz2"))
    zarr_exists = os.path.exists(zarr_path)
    if zarr_exists:
        zarr_dataset = xr.open_zarr(zarr_path, consolidated=True)
        new_compressed_files = []
        for f in compressed_native_files:
            base_filename = f.name
            file_timestep = eumetsat_filename_to_datetime(str(base_filename))
            exists = check_if_timestep_exists(
                pd.Timestamp(file_timestep).round("5 min"), zarr_dataset
            )
            if not exists:
                new_compressed_files.append(f)
        compressed_native_files = new_compressed_files
    # Check if zarr already exists
    if not zarr_exists:
        # Inital zarr path before then appending
        dataset = native_wrapper((compressed_native_files[0], region))
        save_dataset_to_zarr(dataset, zarr_path=zarr_path, zarr_mode="w")

    pool = multiprocessing.Pool(processes=4)
    for dataset in pool.imap_unordered(
        native_wrapper,
        zip(
            compressed_native_files[1:] if not zarr_exists else compressed_native_files,
            repeat(region),
        ),
    ):
        if dataset is not None:
            save_dataset_to_zarr(
                dataset,
                zarr_path=zarr_path,
                x_size_per_chunk=spatial_chunk_size,
                y_size_per_chunk=spatial_chunk_size,
                timesteps_per_chunk=temporal_chunk_size,
            )
        del dataset


def native_wrapper(filename_and_area):
    filename, area = filename_and_area
    return load_native_to_dataset(filename, area)

