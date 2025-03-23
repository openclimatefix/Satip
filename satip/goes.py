"""Classes and methods to provide an interface to the GOES data.

Classes and methods to handle access to GOES satellite imagery data, manage downloads,
and storage of data from sources like Microsoft's Planetary Computer or AWS.

Usage example:
  from satip.goes import GOESDownloadManager
  dm = GOESDownloadManager(download_directory)
"""

import datetime
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import fsspec
import pandas as pd
import requests
import structlog
import xarray as xr

from satip import utils

log = structlog.stdlib.get_logger()

# Microsoft Planetary Computer STAC API endpoint
PLANETARY_COMPUTER_STAC_API = "https://planetarycomputer.microsoft.com/api/stac/v1"

# AWS S3 bucket for GOES data
AWS_GOES_BUCKET = "noaa-goes"


def query_goes_data(
    satellite: str = "G16",  # G16, G17, G18
    product: str = "ABI-L1b-RadF",  # ABI-L1b-RadF, ABI-L1b-RadC, ABI-L2-CMIPF
    start_date: str = "2020-01-01",
    end_date: str = "2020-01-02",
    channels: Optional[List[int]] = None,
) -> List[dict]:
    """
    Query GOES data from Microsoft's Planetary Computer STAC API.

    Args:
        satellite: GOES satellite identifier (G16, G17, G18)
        product: GOES product identifier
        start_date: Start date for the query (YYYY-MM-DD)
        end_date: End date for the query (YYYY-MM-DD)
        channels: List of channels to include (if None, include all)

    Returns:
        List of dictionaries containing metadata for matching GOES data files
    """
    # Format dates for the query
    start_date_dt = pd.to_datetime(start_date)
    end_date_dt = pd.to_datetime(end_date)

    # Construct the STAC API query
    params = {
        "collections": ["goes-" + satellite.lower()],
        "datetime": f"{start_date_dt.isoformat()}/{end_date_dt.isoformat()}",
        "query": {
            "goes:product": {"eq": product}
        },
        "limit": 500
    }

    # Add channel filter if specified
    if channels:
        params["query"]["abi:band"] = {"in": channels}

    # Make the request to the STAC API
    response = requests.post(f"{PLANETARY_COMPUTER_STAC_API}/search", json=params)
    response.raise_for_status()

    # Extract the features from the response
    results = response.json()
    features = results.get("features", [])

    # Handle pagination if there are more results
    while "next" in results.get("links", []):
        next_url = next(link["href"] for link in results["links"] if link["rel"] == "next")
        response = requests.get(next_url)
        response.raise_for_status()
        results = response.json()
        features.extend(results.get("features", []))

    return features


def goes_filename_to_datetime(filename: str) -> datetime.datetime:
    """
    Extract datetime from GOES filename.

    Args:
        filename: GOES filename

    Returns:
        datetime object representing the acquisition time
    """
    # Example filename: OR_ABI-L1b-RadF-M6C01_G16_s20201800000000_e20201800000000_c20201800000000.nc
    pattern = r"_s(\d{14})_"
    match = re.search(pattern, filename)
    if match:
        date_str = match.group(1)
        return datetime.datetime.strptime(date_str, "%Y%j%H%M%S%f")
    else:
        raise ValueError(f"Could not extract datetime from filename: {filename}")


class GOESDownloadManager:
    """
    Manager class for downloading GOES data.
    """

    def __init__(
        self,
        data_dir: str,
        native_file_dir: str = ".",
    ):
        """
        Initialize the GOES download manager.

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
        log.info(f"Downloading file from {url} to {output_path}", parent="GOESDownloadManager")

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
        Download multiple GOES datasets.

        Args:
            datasets: List of dataset metadata dictionaries
            max_workers: Maximum number of concurrent downloads

        Returns:
            List of paths to downloaded files
        """
        if not datasets:
            log.info("No files to download", parent="GOESDownloadManager")
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
                    log.debug(f"File {filename} already exists, skipping", parent="GOESDownloadManager")
                    downloaded_files.append(output_path)
                    continue

                # Check if the file exists in the native file directory
                native_path = os.path.join(self.native_file_dir, filename)
                if os.path.exists(native_path):
                    log.debug(f"Copying file from {native_path} to {output_path}", parent="GOESDownloadManager")
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
                    log.error(f"Error downloading file: {e}", exc_info=True, parent="GOESDownloadManager")

        return downloaded_files

    def download_date_range(
        self,
        satellite: str = "G16",
        product: str = "ABI-L1b-RadF",
        start_date: str = "2020-01-01",
        end_date: str = "2020-01-02",
        channels: Optional[List[int]] = None,
    ) -> List[str]:
        """
        Download GOES data for a specific date range.

        Args:
            satellite: GOES satellite identifier (G16, G17, G18)
            product: GOES product identifier
            start_date: Start date for the query (YYYY-MM-DD)
            end_date: End date for the query (YYYY-MM-DD)
            channels: List of channels to include (if None, include all)

        Returns:
            List of paths to downloaded files
        """
        # Query available datasets
        datasets = query_goes_data(
            satellite=satellite,
            product=product,
            start_date=start_date,
            end_date=end_date,
            channels=channels,
        )

        log.info(f"Found {len(datasets)} datasets for {satellite} {product} from {start_date} to {end_date}",
                parent="GOESDownloadManager")

        # Download the datasets
        return self.download_datasets(datasets)

    def open_goes_dataset(self, file_path: str) -> xr.Dataset:
        """
        Open a GOES NetCDF file as an xarray Dataset.

        Args:
            file_path: Path to the GOES NetCDF file

        Returns:
            xarray Dataset containing the GOES data
        """
        return xr.open_dataset(file_path)

    def convert_to_zarr(
        self,
        files: List[str],
        output_dir: str,
        use_rescaler: bool = True,
    ) -> List[str]:
        """
        Convert GOES NetCDF files to Zarr format.

        Args:
            files: List of paths to GOES NetCDF files
            output_dir: Directory where Zarr files will be saved
            use_rescaler: Whether to rescale data to [0, 1] range

        Returns:
            List of paths to created Zarr files
        """
        zarr_files = []

        for file_path in files:
            try:
                # Open the NetCDF file
                ds = self.open_goes_dataset(file_path)

                # Extract the datetime from the filename
                dt = goes_filename_to_datetime(os.path.basename(file_path))

                # Create a Zarr filename based on the datetime
                zarr_filename = f"goes_{dt.strftime('%Y%m%d%H%M')}.zarr.zip"
                zarr_path = os.path.join(output_dir, zarr_filename)

                # TODO: Implement rescaling similar to EUMETSAT data

                # Save to Zarr format
                utils.save_to_zarr_to_backend(ds, zarr_path)

                zarr_files.append(zarr_path)

                log.info(f"Converted {file_path} to {zarr_path}", parent="GOESDownloadManager")

            except Exception as e:
                log.error(f"Error converting {file_path} to Zarr: {e}", exc_info=True, parent="GOESDownloadManager")

        return zarr_files
