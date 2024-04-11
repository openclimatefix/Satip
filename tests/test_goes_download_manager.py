from datetime import datetime
from satip.goes_download_manager import GOESDownloadManager


# Test case for downloading GOES-15 data from CLAss
def test_download_goes_15_data():
    # Initialize GoesDownloadManager
    download_manager = GOESDownloadManager(data_dir="data")

    # Define time range
    start_date = datetime(2010, 3, 1)
    end_date = datetime(2018, 3, 2)

    # Specify satellite (GOES-15)
    satellite = "15"

    # Download archival GOES-15 data
    download_manager.download_archival_goes_data(start_date, end_date, satellite)
