"""Classes and methods to provide an interface to the Himawari data.

Classes and methods to handle access to Himawari satellite imagery data, manage downloads,
and storage of data from sources like AWS.

Usage example:
  from satip.himawari import HimawariDownloadManager
  dm = HimawariDownloadManager(download_directory)
"""

import datetime
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Union

import fsspec
import pandas as pd
import requests
import structlog
import xarray as xr

from satip import utils
from satip.data_store import dateset_it_to_filename

log = structlog.stdlib.get_logger()

# AWS S3 bucket for Himawari data
AWS_HIMAWARI_BUCKET = "noaa-himawari8"

# Kerchunk dataset URL for Himawari data
KERCHUNK_HIMAWARI_URL = "https://huggingface.co/datasets/jacobbieker/himawari8-kerchunk"


def query_himawari_data(
    product: str = "AHI-L1b-FLDK",  # AHI-L1b-FLDK (Full Disk)
    start_date: str = "2020-01-01",
    end_date: str = "2020-01-02",
    channels: Optional[List[int]] = None,
) -> List[dict]:
    """
    Query Himawari data from AWS S3 bucket.

    Args:
        product: Himawari product identifier
        start_date: Start date for the query (YYYY-MM-DD)
        end_date: End date for the query (YYYY-MM-DD)
        channels: List of channels to include (if None, include all)

    Returns:
        List of dictionaries containing metadata for matching Himawari data files
    """
    # Format dates for the query
    start_date_dt = pd.to_datetime(start_date)
    end_date_dt = pd.to_datetime(end_date)
    
    # Initialize the list to store results
    results = []
    
    # Create a filesystem object for the AWS S3 bucket
    fs = fsspec.filesystem("s3", anon=True)
    
    # Iterate through each day in the date range
    current_date = start_date_dt
    while current_date <= end_date_dt:
        # Construct the prefix for the S3 bucket
        year = current_date.strftime("%Y")
        month = current_date.strftime("%m")
        day = current_date.strftime("%d")
        prefix = f"AHI-L1b-FLDK/{year}/{month}/{day}"
        
        try:
            # List files in the S3 bucket with the given prefix
            files = fs.ls(f"{AWS_HIMAWARI_BUCKET}/{prefix}")
            
            # Filter files by channels if specified
            if channels:
                channel_patterns = [f"_B{ch:02d}_" for ch in channels]
                files = [f for f in files if any(pattern in f for pattern in channel_patterns)]
            
            # Create metadata dictionaries for each file
            for file_path in files:
                filename = os.path.basename(file_path)
                
                # Extract datetime from filename
                dt = himawari_filename_to_datetime(filename)
                
                # Only include files within the specified date range
                if start_date_dt <= dt <= end_date_dt:
                    results.append({
                        "id": filename,
                        "datetime": dt.isoformat(),
                        "assets": {
                            "data": {
                                "href": f"s3://{AWS_HIMAWARI_BUCKET}/{file_path}"
                            }
                        }
                    })
        
        except Exception as e:
            log.error(f"Error querying Himawari data for {current_date.date()}: {e}", exc_info=True)
        
        # Move to the next day
        current_date += datetime.timedelta(days=1)
    
    # Sort results by datetime
    results.sort(key=lambda x: x["datetime"])
    
    return results


def himawari_filename_to_datetime(filename: str) -> datetime.datetime:
    """
    Extract datetime from Himawari filename.

    Args:
        filename: Himawari filename

    Returns:
        datetime object representing the acquisition time
    """
    # Example filename: HS_H08_20200101_0000_B01_FLDK_R20_S0110.nc
    pattern = r"HS_H\d+_(\d{8})_(\d{4})_"
    match = re.search(pattern, filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        return datetime.datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M")
    else:
        raise ValueError(f"Could not extract datetime from filename: {filename}")


class HimawariDownloadManager:
    """
    Manager class for downloading Himawari data.
    """

    def __init__(
        self,
        data_dir: str,
        native_file_dir: str = ".",
    ):
        """
        Initialize the Himawari download manager.

        Args:
            data_dir: Path to the directory where the satellite data will be saved
            native_file_dir: Path where the native files are saved
        """
        # Configure the data directory
        self.data_dir = data_dir
        self.native_file_dir = native_file_dir

        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
            except PermissionError:
                raise PermissionError(f"No permission to create {self.data_dir}.")

    def download_single_file(self, url: str, output_path: str) -> None:
        """
        Download a single file from a URL.

        Args:
            url: URL of the file to download
            output_path: Path where the file will be saved
        """
        log.info(f"Downloading file from {url} to {output_path}", parent="HimawariDownloadManager")
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Download the file
        with fsspec.open(url, "rb") as src:
            with open(output_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

    def download_datasets(
        self,
        datasets: List[dict],
        max_workers: int = 4,
    ) -> List[str]:
        """
        Download multiple Himawari datasets.

        Args:
            datasets: List of dataset metadata dictionaries
            max_workers: Maximum number of concurrent downloads

        Returns:
            List of paths to downloaded files
        """
        if not datasets:
            log.info("No files to download", parent="HimawariDownloadManager")
            return []

        downloaded_files = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for dataset in datasets:
                # Get the download URL from the dataset metadata
                href = dataset["assets"]["data"]["href"]
                
                # Extract the filename from the URL
                filename = os.path.basename(href)
                
                # Check if the file already exists in the data directory
                output_path = os.path.join(self.data_dir, filename)
                
                if os.path.exists(output_path):
                    log.debug(f"File {filename} already exists, skipping", parent="HimawariDownloadManager")
                    downloaded_files.append(output_path)
                    continue
                
                # Check if the file exists in the native file directory
                native_path = os.path.join(self.native_file_dir, filename)
                if os.path.exists(native_path):
                    log.debug(f"Copying file from {native_path} to {output_path}", parent="HimawariDownloadManager")
                    shutil.copy(native_path, output_path)
                    downloaded_files.append(output_path)
                    continue
                
                # Submit the download task to the executor
                futures.append(executor.submit(self.download_single_file, href, output_path))
                
            # Wait for all downloads to complete
            for future in as_completed(futures):
                try:
                    future.result()
                    downloaded_files.append(output_path)
                except Exception as e:
                    log.error(f"Error downloading file: {e}", exc_info=True, parent="HimawariDownloadManager")
        
        return downloaded_files

    def download_date_range(
        self,
        product: str = "AHI-L1b-FLDK",
        start_date: str = "2020-01-01",
        end_date: str = "2020-01-02",
        channels: Optional[List[int]] = None,
    ) -> List[str]:
        """
        Download Himawari data for a specific date range.

        Args:
            product: Himawari product identifier
            start_date: Start date for the query (YYYY-MM-DD)
            end_date: End date for the query (YYYY-MM-DD)
            channels: List of channels to include (if None, include all)

        Returns:
            List of paths to downloaded files
        """
        # Query available datasets
        datasets = query_himawari_data(
            product=product,
            start_date=start_date,
            end_date=end_date,
            channels=channels,
        )
        
        log.info(f"Found {len(datasets)} datasets for Himawari {product} from {start_date} to {end_date}", 
                parent="HimawariDownloadManager")
        
        # Download the datasets
        return self.download_datasets(datasets)

    def open_himawari_dataset(self, file_path: str) -> xr.Dataset:
        """
        Open a Himawari NetCDF file as an xarray Dataset.

        Args:
            file_path: Path to the Himawari NetCDF file

        Returns:
            xarray Dataset containing the Himawari data
        """
        return xr.open_dataset(file_path)

    def convert_to_zarr(
        self,
        files: List[str],
        output_dir: str,
        use_rescaler: bool = True,
    ) -> List[str]:
        """
        Convert Himawari NetCDF files to Zarr format.

        Args:
            files: List of paths to Himawari NetCDF files
            output_dir: Directory where Zarr files will be saved
            use_rescaler: Whether to rescale data to [0, 1] range

        Returns:
            List of paths to created Zarr files
        """
        zarr_files = []
        
        for file_path in files:
            try:
                # Open the NetCDF file
                ds = self.open_himawari_dataset(file_path)
                
                # Extract the datetime from the filename
                dt = himawari_filename_to_datetime(os.path.basename(file_path))
                
                # Create a Zarr filename based on the datetime
                zarr_filename = f"himawari_{dt.strftime('%Y%m%d%H%M')}.zarr.zip"
                zarr_path = os.path.join(output_dir, zarr_filename)
                
                # TODO: Implement rescaling similar to EUMETSAT data
                
                # Save to Zarr format
                utils.save_to_zarr_to_backend(ds, zarr_path)
                
                zarr_files.append(zarr_path)
                
                log.info(f"Converted {file_path} to {zarr_path}", parent="HimawariDownloadManager")
                
            except Exception as e:
                log.error(f"Error converting {file_path} to Zarr: {e}", exc_info=True, parent="HimawariDownloadManager")
        
        return zarr_files

    def open_kerchunk_dataset(self, date: Union[str, datetime.datetime]) -> xr.Dataset:
        """
        Open a Himawari dataset from the Kerchunk reference.
        
        This uses the Kerchunk references created by Jacob Bieker and hosted on Hugging Face.

        Args:
            date: Date to retrieve data for

        Returns:
            xarray Dataset containing the Himawari data
        """
        # Convert date to datetime if it's a string
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        # Format the date for the Kerchunk reference
        date_str = date.strftime("%Y%m%d")
        
        # Construct the URL for the Kerchunk reference
        kerchunk_url = f"{KERCHUNK_HIMAWARI_URL}/resolve/main/references/{date_str}.json"
        
        try:
            # Open the dataset using the Kerchunk reference
            mapper = fsspec.filesystem("reference", fo=kerchunk_url)
            ds = xr.open_dataset(mapper.get_mapper(), engine="zarr")
            return ds
        except Exception as e:
            log.error(f"Error opening Kerchunk dataset for {date_str}: {e}", exc_info=True)
            raise