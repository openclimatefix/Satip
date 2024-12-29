"""Unit Tests for satip.eumetsat."""
import glob
import os
import tempfile
from datetime import datetime, timezone, timedelta
import pandas as pd

from satip.eumetsat import EUMETSATDownloadManager, eumetsat_filename_to_datetime

def test_filename_to_datetime():
    """If there were a test here, there would also be a docstring here."""
    filename = "MSG4-SEVI-MSG15-0000-NA-20230814075918.739000000Z-NA"
    expected_datetime = datetime(2023, 8, 14, 7, 59, 18)
    actual_datetime = eumetsat_filename_to_datetime(filename)
    assert actual_datetime == expected_datetime
    filename = "MSG4-SEVI-MSG15-0100-NA-20230814085917.262000000Z-NA"
    expected_datetime = datetime(2023, 8, 14, 8, 59, 17)
    actual_datetime = eumetsat_filename_to_datetime(filename)
    assert actual_datetime == expected_datetime
