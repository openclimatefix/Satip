""" Function to do with filenames """
import pandas as pd


def get_datetime_from_filename(
    filename: str, strip_hrv: bool = False, strip_15: bool = False
) -> pd.Timestamp:
    """Extract time from filename

    For example:
    - folder/iodc_202408281115.zarr.zip
    - folder/202006011205.zarr.zip
    - folder/hrv_202408261815.zarr.zip
    - folder/15_hrv_202408261815.zarr.zip
    """

    filename = filename.replace("iodc_", "")

    if strip_15:
        filename = filename.replace("15_", "")

    if strip_hrv:
        filename = filename.replace("hrv_", "")

    filename = filename.split(".zarr.zip")[0]
    date = filename.split("/")[-1]

    try:
        file_time = pd.to_datetime(date, format="%Y%m%d%H%M", utc=True)
    except Exception:
        # Replicating deprecated "errors=ignore" behaviour
        # Probably want to actually do something about this
        file_time = date

    return file_time
