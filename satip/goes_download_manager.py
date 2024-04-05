"""
Script for downloading GOES data.
"""

import datetime
import logging
import os

import requests
from goes2go import GOES


class GOESDownloadManager:
    """
    Manager class for downloading GOES data.
    """
    def __init__(self, data_dir, log_directory=None):
        """
        Initialize the GOESDownloadManager.

        Args:
            data_dir (str): Directory to save downloaded GOES data.
            log_directory (str, optional): Directory to save logs.
            If None, logging is printed to STDOUT.
        """
        self.data_dir = data_dir
        self.ensure_directory_exists(self.data_dir)

        if log_directory:
            self.ensure_directory_exists(log_directory)
            logging.basicConfig(
                filename=os.path.join(log_directory, 'goes_download.log'),
                level=logging.INFO)
        else:
            logging.basicConfig(level=logging.INFO)

        logging.info(f"GOESDownloadManager initialized. Data will be saved to: {data_dir}")

    @staticmethod
    def ensure_directory_exists(directory):
        """Ensures the specified directory exists, creating it if necessary."""
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logging.info(f"Created directory: {directory}")
            except Exception as e:
                logging.error(f"Error creating directory {directory}: {e}")
                raise
    def download_goes_data(self, start_time, end_time, product='ABI-L1b-RadC',
                       domain='F', satellite=16):
        """
        Download GOES data for a specified time range and product.

        Args:
            start_time (datetime): Start of the download period.
            end_time (datetime): End of the download period.
            product (str): GOES product identifier. Default is 'ABI-L1b-RadC'.
            domain (str): Domain for the product. Default is 'F' (Full Disk).
            satellite (int): GOES satellite number. Default is 16.
        """
        G = GOES(satellite=satellite, product=product, domain=domain)
        current_time = start_time

        # Determine time increment based on product/domain
        time_increment = 1  # Default time increment (minutes)
        if product == 'ABI-L1b-RadC' and domain == 'F':
            time_increment = 10

        while current_time <= end_time:
            try:
                # Download the data
                ds = G.nearesttime(current_time)

                # Get acquisition time from the dataset
                acquisition_time = ds.time.data.item()

                # Format the acquisition time for filename
                date_string = acquisition_time.strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"goes_data_{date_string}.nc"
                filepath = os.path.join(self.data_dir, filename)

                # Check if data for current acquisition time already exists
                if os.path.exists(filepath):
                    logging.info(f"Data for {date_string} already exists. Skipping.")
                    current_time += datetime.timedelta(minutes=time_increment)
                    continue

                # Save to NetCDF
                ds.to_netcdf(filepath)

                logging.info(f"Downloaded and saved GOES data to: {filename}")
            except Exception as e:
                logging.error(f"Error downloading GOES data for {current_time}: {e}")

            current_time += datetime.timedelta(minutes=time_increment)

        logging.info("Completed GOES data download.")

    def check_url_for_goes_data(self, url):
        """
        Check if the provided URL contains the GOES-8 to GOES-15 data.
        """
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            return False

    def download_archival_goes_data(self, start_date, end_date, satellite):
        """
        Download archival GOES data for a specified time range and satellite.

        Args:
            start_date (datetime): Start of the download period.
            end_date (datetime): End of the download period.
            satellite (str): GOES satellite range,
            e.g., '8-15' for GOES-8 to GOES-15 or '15' for GOES-15.
        """
        # Construct base URL
        base_url = "https://www.aev.class.noaa.gov/saa/products/search?datatype_family=GVAR_IMG"

        # Check if the provided URL contains the desired data
        if self.check_url_for_goes_data(base_url):
            # If satellite is a range
            if '-' in satellite:
                # Extract start and end satellite numbers
                start_satellite, end_satellite = map(int, satellite.split('-'))

                # Iterate over the range of satellites
                for sat_num in range(start_satellite, end_satellite + 1):
                    # Construct URL for each satellite
                    url = f"{base_url}/GOES-{sat_num}"
                    print(f"Checking data availability for GOES-{sat_num}...")

                    # Download data
                    print(f"Downloading archival data from {url}...")
                    response = requests.get(url)

                    if response.status_code == 200:
                        # Save data to file
                        output_file = os.path.join(self.data_dir,
                                                   f"goes_archival_data_{sat_num}.nc")
                        with open(output_file, 'wb') as f:
                            f.write(response.content)
                        print(f"Archival data saved to {output_file}")
                    else:
                        print(f"Failed to download archival data for GOES-{sat_num}.")
            else:
                # Extract satellite number
                sat_num = int(satellite)

                # Construct URL for the specified satellite
                url = f"{base_url}/GOES-{sat_num}"
                print(f"Checking data availability for GOES-{sat_num}...")

                # Download data
                print(f"Downloading archival data from {url}...")
                response = requests.get(url)

                if response.status_code == 200:
                    # Save data to file
                    output_file = os.path.join(self.data_dir, f"goes_archival_data_{sat_num}.nc")
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    print(f"Archival data saved to {output_file}")
                else:
                    print(f"Failed to download archival data for GOES-{sat_num}.")
        else:
            print("The URL does not contain the desired GOES data")
