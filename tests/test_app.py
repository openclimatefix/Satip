import os
from satip.eumetsat import DownloadManager
from satip.utils import save_native_to_netcdf
import pandas as pd
import glob


def test_saving_netcdf():
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    download_manager = DownloadManager(user_key=user_key, user_secret=user_secret, data_dir=os.getcwd())
    download_manager.download_date_range(
        start_date=(pd.Timestamp().now() - pd.Timedelta("1 hour")).strftime("%Y-%m-%d-%H-%M-%S"),
        end_date=pd.Timestamp().now().strftime("%Y-%m-%d-%H-%M-%S"),
    )

    # 2. Load grib files to one Xarray Dataset
    native_files = list(glob.glob(os.path.join(os.getcwd(), "*.nat")))
    # data = datahub.load_all_files()
    save_native_to_netcdf(native_files, save_dir=os.getcwd())
    assert len(native_files) > 0
    assert os.path.exists(os.path.join(os.getcwd(), "latest.nc"))
    assert os.path.exists(os.path.join(os.getcwd(), "hrv_latest.nc"))
