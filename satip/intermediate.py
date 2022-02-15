"""Handles XArray data generation/updating/splitting from files.

Methods here pre-process file-based data and handle
... generation of XArray Dataset files from data files
... updating of XArray Dataset files from data files
... splitting XArray Dataset files by month

Usage examples:
  split_per_month(*args, **kwargs)
  cloudmask_split_per_month(*args, **kwargs)
  create_or_update_zarr_with_native_files(*args, **kwargs)
  create_or_update_zarr_with_cloud_mask_files(*args, **kwargs)
"""
# TODO: Replace print-statements with a properly configured logger

import multiprocessing
import os
from itertools import repeat
from pathlib import Path

import pandas as pd
import xarray as xr
from tqdm import tqdm

from satip.eumetsat import eumetsat_cloud_name_to_datetime, eumetsat_filename_to_datetime
from satip.utils import (
    check_if_timestep_exists,
    load_cloudmask_to_dataset,
    load_native_to_dataset,
    save_dataset_to_zarr,
)


def split_per_month(
    directory: str,
    zarr_path: str,
    hrv_zarr_path: str,
    region: str,
    temp_directory: str = "/mnt/ramdisk/",
    spatial_chunk_size: int = 512,
    temporal_chunk_size: int = 1,
):
    """
    Splits the Zarr creation into multiple, month-long Zarr files for parallel writing

    Args:
        directory: Top-level directory containing the compressed native files
        zarr_path: Path of the final Zarr file
        hrv_zarr_path: Path of the final HRV-Zarr-file
        region: Name of the region to keep for the datastore
        temp_directory: Temporary directory to store files to before they are moved
                        to their final location once they passed the checks.
        spatial_chunk_size: Chunk size, in pixels in the x  and y directions, passed to Xarray
        temporal_chunk_size: Chunk size, in timesteps, for saving into the zarr file

    """

    # Get year
    temp_directory = Path(temp_directory)
    year_directories = os.listdir(directory)
    print(year_directories)
    dirs = []
    zarrs = []
    hrv_zarrs = []
    for year in year_directories:
        if not os.path.isdir(os.path.join(directory, year)):
            continue
        month_directories = os.listdir(os.path.join(directory, year))
        for month in month_directories:
            if not os.path.isdir(os.path.join(directory, year, month)):
                continue
            month_directory = os.path.join(directory, year.split("/")[0], month.split("/")[0])
            month_zarr_path = zarr_path + f"_{year.split('/')[0]}_{month.split('/')[0]}.zarr"
            hrv_month_zarr_path = (
                hrv_zarr_path + f"_{year.split('/')[0]}" f"_{month.split('/')[0]}.zarr"
            )
            dirs.append(month_directory)
            zarrs.append(month_zarr_path)
            hrv_zarrs.append(hrv_month_zarr_path)
            zarr_exists = os.path.exists(month_zarr_path)
            if not zarr_exists:
                # Inital zarr path before then appending
                compressed_native_files = sorted(list(Path(month_directory).rglob("*.bz2")))
                if len(compressed_native_files) == 0:
                    continue
                dataset, hrv_dataset = load_native_to_dataset(
                    compressed_native_files[0], temp_directory, region, calculate_osgb=True
                )
                save_dataset_to_zarr(
                    dataset,
                    zarr_path=month_zarr_path,
                    compressor_name="jpeg-xl",
                    zarr_mode="w",
                    x_size_per_chunk=spatial_chunk_size,
                    y_size_per_chunk=spatial_chunk_size,
                    timesteps_per_chunk=temporal_chunk_size,
                )
                save_dataset_to_zarr(
                    hrv_dataset,
                    zarr_path=hrv_month_zarr_path,
                    compressor_name="jpeg-xl",
                    zarr_mode="w",
                    x_size_per_chunk=spatial_chunk_size,
                    y_size_per_chunk=spatial_chunk_size,
                    timesteps_per_chunk=temporal_chunk_size,
                )
    print(dirs)
    print(zarrs)
    pool = multiprocessing.Pool(processes=os.cpu_count())
    for _ in tqdm(
        pool.imap_unordered(
            _wrapper_create_or_update_xarr_with_native_files,
            zip(
                dirs,
                zarrs,
                hrv_zarrs,
                repeat(temp_directory),
                repeat(region),
                repeat(spatial_chunk_size),
                repeat(temporal_chunk_size),
            ),
        )
    ):
        print("Month done")


def _wrapper_create_or_update_xarr_with_native_files(args):
    dirs, zarrs, hrv_zarrs, temp_directory, region, spatial_chunk_size, temporal_chunk_size = args
    create_or_update_zarr_with_native_files(
        dirs, zarrs, hrv_zarrs, temp_directory, region, spatial_chunk_size, temporal_chunk_size
    )


def cloudmask_split_per_month(
    directory: str,
    zarr_path: str,
    region: str,
    temp_directory: str = "/mnt/ramdisk/",
    spatial_chunk_size: int = 512,
    temporal_chunk_size: int = 1,
):
    """
    Splits the Zarr creation into multiple, month-long Zarr files for parallel writing

    Args:
        directory: Top-level directory containing the compressed native files
        zarr_path: Path of the final Zarr file
        region: Name of the region to keep for the datastore
        temp_directory: Temporary directory to store files to before they are moved
                        to their final location once they passed the checks.
        spatial_chunk_size: Chunk size, in pixels in the x and y directions, passed to Xarray
        temporal_chunk_size: Chunk size, in timesteps, for saving into the zarr file

    """

    # Get year
    temp_directory = Path(temp_directory)
    year_directories = os.listdir(directory)
    print(year_directories)
    dirs = []
    zarrs = []
    for year in year_directories:
        if not os.path.isdir(os.path.join(directory, year)):
            continue
        month_directories = os.listdir(os.path.join(directory, year))
        for month in month_directories:
            if not os.path.isdir(os.path.join(directory, year, month)):
                continue
            month_directory = os.path.join(directory, year.split("/")[0], month.split("/")[0])
            month_zarr_path = zarr_path + f"_{year.split('/')[0]}_{month.split('/')[0]}.zarr"
            dirs.append(month_directory)
            zarrs.append(month_zarr_path)
            zarr_exists = os.path.exists(month_zarr_path)
            if not zarr_exists:
                # Inital zarr path before then appending
                compressed_native_files = list(Path(month_directory).rglob("*.grb"))
                dataset = load_cloudmask_to_dataset(
                    compressed_native_files[0], temp_directory, region, calculate_osgb=True
                )
                save_dataset_to_zarr(
                    dataset,
                    zarr_path=month_zarr_path,
                    compressor_name="bz2",
                    x_size_per_chunk=spatial_chunk_size,
                    y_size_per_chunk=spatial_chunk_size,
                    timesteps_per_chunk=temporal_chunk_size,
                    zarr_mode="w",
                )
    print(dirs)
    print(zarrs)
    pool = multiprocessing.Pool(processes=os.cpu_count())
    for _ in tqdm(
        pool.imap_unordered(
            _cloudmask_wrapper,
            zip(
                dirs,
                zarrs,
                repeat(temp_directory),
                repeat(region),
                repeat(spatial_chunk_size),
                repeat(temporal_chunk_size),
            ),
        )
    ):
        print("Month done")


def _cloudmask_wrapper(args):
    dirs, zarrs, temp_directory, region, spatial_chunk_size, temporal_chunk_size = args
    create_or_update_zarr_with_cloud_mask_files(
        dirs, zarrs, temp_directory, region, spatial_chunk_size, temporal_chunk_size
    )


def create_or_update_zarr_with_cloud_mask_files(
    directory: str,
    zarr_path: str,
    temp_directory: Path,
    region: str,
    spatial_chunk_size: int = 256,
    temporal_chunk_size: int = 1,
) -> None:
    """
    Creates or updates a zarr file with the cloud mask files

    Args:
        directory: Top-level directory containing the compressed native files
        zarr_path: Path of the final Zarr file
        temp_directory: Temporary directory to store files to before they are moved
                        to their final location once they passed the checks.
        region: Name of the region to keep for the datastore
        spatial_chunk_size: Chunk size, in pixels in the x  and y directions, passed to Xarray
        temporal_chunk_size: Chunk size, in timesteps, for saving into the zarr file
    """
    # Satpy Scene doesn't do well with fsspec
    grib_files = sorted(list(Path(directory).rglob("*.grb")))
    zarr_exists = os.path.exists(zarr_path)
    if zarr_exists:
        zarr_dataset = xr.open_zarr(zarr_path, consolidated=True)
        new_compressed_files = []
        for f in grib_files:
            base_filename = f.name
            file_timestep = eumetsat_cloud_name_to_datetime(str(base_filename))
            exists = check_if_timestep_exists(
                pd.Timestamp(file_timestep).round("5 min"), zarr_dataset
            )
            if not exists:
                new_compressed_files.append(f)
        grib_files = new_compressed_files
    # Check if zarr already exists
    for entry in tqdm(grib_files):
        try:
            dataset = load_cloudmask_to_dataset(entry, temp_directory, region, calculate_osgb=False)
            if dataset is not None:
                try:
                    save_dataset_to_zarr(
                        dataset,
                        zarr_path=zarr_path,
                        compressor_name="bz2",
                        x_size_per_chunk=spatial_chunk_size,
                        y_size_per_chunk=spatial_chunk_size,
                        timesteps_per_chunk=temporal_chunk_size,
                    )
                except Exception as e:
                    print(f"Failed with: {e}")
            del dataset
        except Exception as e:
            print(f"Failed with Exception with {e}")


def create_or_update_zarr_with_native_files(
    directory: str,
    zarr_path: str,
    hrv_zarr_path: str,
    temp_directory: Path,
    region: str,
    spatial_chunk_size: int = 256,
    temporal_chunk_size: int = 1,
) -> None:
    """
    Creates or updates a zarr file with satellite native files

    Args:
        directory: Top-level directory containing the compressed native files
        zarr_path: Path of the final Zarr file
        hrv_zarr_path: Path for the final HRV-Zarr-file
        temp_directory: Temporary directory to store files to before they are moved
                        to their final location once they passed the checks.
        region: Name of the region to keep for the datastore
        spatial_chunk_size: Chunk size, in pixels in the x  and y directions, passed to Xarray
        temporal_chunk_size: Chunk size, in timesteps, for saving into the zarr file

    """

    # Satpy Scene doesn't do well with fsspec
    compressed_native_files = sorted(list(Path(directory).rglob("*.bz2")))
    if len(compressed_native_files) == 0:
        return
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
    for entry in tqdm(compressed_native_files):
        try:
            dataset, hrv_dataset = load_native_to_dataset(
                entry, temp_directory, region, calculate_osgb=False
            )
            if dataset is not None and hrv_dataset is not None:
                try:
                    save_dataset_to_zarr(
                        dataset,
                        zarr_path=zarr_path,
                        compressor_name="jpeg-xl",
                        x_size_per_chunk=spatial_chunk_size,
                        y_size_per_chunk=spatial_chunk_size,
                        timesteps_per_chunk=temporal_chunk_size,
                    )
                    save_dataset_to_zarr(
                        hrv_dataset,
                        zarr_path=hrv_zarr_path,
                        compressor_name="jpeg-xl",
                        x_size_per_chunk=spatial_chunk_size,
                        y_size_per_chunk=spatial_chunk_size,
                        timesteps_per_chunk=temporal_chunk_size,
                    )
                except Exception as e:
                    print(f"Failed with: {e}")
            del dataset
            del hrv_dataset
        except Exception as e:
            print(f"Failed with Exception with {e}")


# TODO: Not used in the repo, remove?
def pool_init(q):
    """Initialies a global process queue for the worker."""
    global processed_queue  # make queue global in workers
    processed_queue = q


# TODO: Not used in the repo, remove?
def native_wrapper(filename_and_area):
    """Puts the data-load-job into the global worker queue."""
    filename, area = filename_and_area
    processed_queue.put(load_native_to_dataset(filename, area))
