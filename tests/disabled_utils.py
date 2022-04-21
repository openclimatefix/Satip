"""Tests for the Satip-utils.

Please note that at the moment, these tests are marked disabled for two reasons:
a) There is a weird installation-bug which makes it such that on identical github-workflows,
   script.generate_test_plots runs while this code here seems to draw from the wrong library.
b) We want to have script.generate_test_plots as our try-it-out-script for new users, so
   we have to test that. Though that means that utils gets tested as well, individual
   util-tests seem redundant.
"""
import glob
import os
import unittest
from pathlib import Path

import xarray

from satip.utils import load_cloudmask_to_dataset, load_native_to_dataset, save_dataset_to_zarr

USER_KEY = os.environ.get("EUMETSAT_USER_KEY")
USER_SECRET = os.environ.get("EUMETSAT_USER_SECRET")
RSS_ID = "EO:EUM:DAT:MSG:MSG15-RSS"
CLOUD_ID = "EO:EUM:DAT:MSG:RSS-CLM"


class TestSatipUtils(unittest.TestCase):
    """Tests for satip.utils."""

    def setUp(self) -> None:  # noqa D102
        # If there is no downloaded RSS-data-set or cloudmask, then download and store them:
        if len(list(glob.glob(os.path.join(os.getcwd(), "*.nat")))) == 0:
            from satip import eumetsat

            download_manager = eumetsat.DownloadManager(
                user_key=USER_KEY,
                user_secret=USER_SECRET,
                data_dir=os.getcwd(),
                logger_name="Plotting_test",
            )

            # Download one set of RSS data and one cloudmask and store them on disk:
            download_manager.download_date_range(
                start_date="2020-06-01 11:59:00", end_date="2020-06-01 12:00:00", product_id=RSS_ID
            )
            download_manager.download_date_range(
                start_date="2020-06-01 11:59:00",
                end_date="2020-06-01 12:02:00",
                product_id=CLOUD_ID,
            )

        # Now that we can be sure that those files exist, we can store the filenames.
        # Note: The following fields should now contain the full paths to RSS/cloudmask-data.
        # As per 01.03.2022, given above date-range, the files you got should be:
        # - [path]/MSG3-SEVI-MSG15-0100-NA-20200601115916.810000000Z-NA.nat for the RSS-data
        # - [path]/MSG3-SEVI-MSGCLMK-0100-0100-20200601120000.000000000Z-NA.grb for the cloudmask
        # However, there is no guarantee that future API-releases will keep the naming stable.
        self.rss_filename = list(glob.glob(os.path.join(os.getcwd(), "*.nat")))[0]
        self.cloud_mask_filename = list(glob.glob(os.path.join(os.getcwd(), "*.grb")))[0]

        return super().setUp()

    def test_load_cloudmask_to_dataset(self):  # noqa D102
        for area in ["UK", "RSS"]:
            cloudmask_dataset = load_cloudmask_to_dataset(
                Path(self.cloud_mask_filename), temp_directory=Path(os.getcwd()), area=area
            )
            self.assertEqual(type(cloudmask_dataset), xarray.DataArray)

    def test_load_native_to_dataset(self):  # noqa D102
        for area in ["UK", "RSS"]:
            rss_dataset, hrv_dataset = load_native_to_dataset(
                Path(self.rss_filename), temp_directory=Path(os.getcwd()), area=area
            )
            self.assertEqual(type(rss_dataset), xarray.DataArray)
            self.assertEqual(type(hrv_dataset), xarray.DataArray)

    def test_save_dataset_to_zarr(self):  # noqa D102
        # The following is a bit ugly, but since we do not want to lump two tests into one
        # test function but save_dataset_to_zarr depends on a dataset being loaded,
        # we have to reload the dataset here. This means that this test can theoretically
        # fail for two reasons: Either the data-loading failed, or the data-saving failed.
        rss_dataset, _ = load_native_to_dataset(
            Path(self.rss_filename), temp_directory=Path(os.getcwd()), area="UK"
        )

        zarr_path = os.path.join(os.getcwd(), "tmp.zarr")

        save_dataset_to_zarr(
            rss_dataset,
            zarr_path=zarr_path,
            compressor_name="bz2",
            zarr_mode="w",
        )
        self.assertEqual(1, len(list(glob.glob(zarr_path))))
