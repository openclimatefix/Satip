"""Satip Download Manager

This module provides a unified interface for downloading EUMETSAT and GOES
satellite data via the `DownloadManager` class. Users specify the provider
('EUMETSAT' or 'GOES'), and the manager delegates tasks to dedicated
sub-modules for retrieval, storage, and logging.

Key functionalities:

* Download data for a specified time range.
* Handle user authentication (for EUMETSAT data).
* Manage data retrieval, storage, and logging for both providers.
"""

import warnings

import structlog

log = structlog.stdlib.get_logger()

# Suppress FutureWarning related to 'H' argument
warnings.filterwarnings('ignore', category=FutureWarning)
# constants for different data sources
EUMETSAT_PROVIDER = "EUMETSAT"
GOES_PROVIDER = "GOES"



class DownloadManager:
    """
    Main download manager class to handle both EUMETSAT

    and GOES data downloading based on the provider.

    Example usage:

    if __name__ == "__main__":
        provider = "GOES"
        user_key = "your_user_key"
        user_secret = "your_user_secret"
        data_dir = "path to data directory"
        log_directory = "path to log directory"

        start_time = datetime.datetime(2024, 3, 1, 0, 0)
        end_time = datetime.datetime(2024, 3, 1, 6, 0)

        if data_dir is not None:
            manager = DownloadManager(provider, None, None, data_dir, log_directory)
            manager.download_data(start_time, end_time)
        else:
            print("Error: 'data_dir' is not properly set.")

    """

    def __init__(self, provider: str = "EUMETSAT", user_key=None,
                user_secret=None, data_dir=None,
                log_directory=None):
        """
        Initialize the DownloadManager.

        Args:
            provider (str): Provider name ('EUMETSAT' or 'GOES').
            user_key (str): User key for accessing data (for EUMETSAT).
            user_secret (str): User secret for accessing data (for EUMETSAT).
            data_dir (str): Directory to save downloaded data.
            log_directory (str): Directory to save logs.
        """
        self.provider = provider

        if self.provider == "EUMETSAT":
            from satip.eumetsat import EUMETSATDownloadManager
            self.download_manager = EUMETSATDownloadManager(user_key, user_secret,
                                                            data_dir, log_directory)
        elif self.provider == "GOES":
            from satip.goes_download_manager import GOESDownloadManager
            self.download_manager = GOESDownloadManager(data_dir, log_directory)
        else:
            raise ValueError("Invalid provider. Supported providers are 'EUMETSAT' and 'GOES'.")

    def download_data(self, start_time, end_time):
        """
        Download data for the specified time range.

        Args:
            start_time (datetime): Start of the download period.
            end_time (datetime): End of the download period.
        """
        if self.provider == "GOES":
            self.download_manager.download_goes_data(start_time, end_time)
