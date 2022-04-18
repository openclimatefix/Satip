"""Tests for satip.download.py."""
import os
import unittest

import pandas as pd

from satip.download import _determine_datetimes_to_download_files, download_eumetsat_data
from satip.utils import format_dt_str


class TestDownload(unittest.TestCase):
    """Test case for downloader tests."""

    def setUp(self) -> None:  # noqa
        return super().setUp()

    def test_download_eumetsat_data(self):  # noqa
        # Call the downloader on a very short chunk of data:
        self.assertIsNone(
            download_eumetsat_data(
                download_directory=str(os.getcwd() + "/storage/"),
                start_date=format_dt_str("2020-06-01 11:59:00"),
                end_date=format_dt_str("2020-06-01 12:02:00"),
                user_key=os.environ.get("EUMETSAT_USER_KEY"),
                user_secret=os.environ.get("EUMETSAT_USER_SECRET"),
                auth_filename=None,
                number_of_processes=2,
                product=["cloud", "rss"],
                enforce_full_days=False,
            )
        )

    def test_determine_datetime_to_download_files(self):
        """Tests correct day-wise-chunked lists.

        Given an empty directory, the function is supposed to return a complete
        list of dates, chunked into daily intervals.
        """
        datetimes = _determine_datetimes_to_download_files(
            ".",
            start_date=pd.to_datetime("2020-03-08 12:00"),
            end_date=pd.to_datetime("2020-03-10 09:00"),
            product_id="dummy",
        )
        print(datetimes)
        print(datetimes[0])
        print(type(datetimes[0][0]))
        self.assertEqual(datetimes[0][0], pd.to_datetime("2020-03-08 11:59:00"))
        self.assertEqual(datetimes[0][1], pd.to_datetime("2020-03-09 11:58:00"))
        self.assertEqual(datetimes[1][0], pd.to_datetime("2020-03-09 11:59:00"))
        self.assertEqual(datetimes[1][1], pd.to_datetime("2020-03-10 11:58:00"))
