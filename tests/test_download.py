"""Tests for satip.download.py."""
import os
import unittest

from satip.download import download_eumetsat_data
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
                product=["cloud"],
                enforce_full_days=False,
            )
        )
