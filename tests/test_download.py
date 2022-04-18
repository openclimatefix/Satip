"""Tests for satip.download.py."""
import os
import unittest

import pandas as pd

from satip.download import (
    _determine_datetimes_to_download_files,
    _get_missing_datetimes_from_list_of_files,
    download_eumetsat_data,
)
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

    def test_get_missing_datetimes_from_list_of_files(self):
        """Tests padding of datetimes if files present are missing data for given days."""
        # Assume we only have two files present, as something went very wrong
        # with the download.
        filenames = [
            "MSG3-SEVI-MSG15-0100-NA-20190308114036.810000000Z-NA.nat",
            "MSG3-SEVI-MSG15-0100-NA-20220308133711.810000000Z-NA.nat",
        ]

        # We then expect the function to pad this by adding missing timeranges
        # to fill up everything from the beginning to the first day to the timestamp
        # of the first day (case A), then everything between both files (case B)
        # and finally fill up the rest until the end of the second day (case C).
        expected_timestamps = [
            (pd.to_datetime("2019-03-08 00:00:00"), pd.to_datetime("2019-03-08 11:40:00")),
            (pd.to_datetime("2019-03-08 11:40:00"), pd.to_datetime("2022-03-08 13:37:00")),
            (pd.to_datetime("2022-03-08 13:37:00"), pd.to_datetime("2022-03-08 23:58:00")),
        ]

        # Generate the list of missing datetime interval boundaries:
        res = _get_missing_datetimes_from_list_of_files(filenames)

        for i, interval in enumerate(expected_timestamps):
            for b, boundary in enumerate(interval):
                # Note that the function returns datetime-objects, but we defined the expected
                # values as pd-datetime. Though their str-repr is different, they still pass
                # the equality-check when compared for same dates.
                self.assertEqual(boundary, res[i][b])
