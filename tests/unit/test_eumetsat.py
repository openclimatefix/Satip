"""Tests for satip.eumetsat."""
import glob
import os
import tempfile
from datetime import datetime, timezone, timedelta

from satip.eumetsat import DownloadManager

from .conftest import mocked_requests_get, mocked_requests_post, mocked_requests_patch
from unittest import mock

# import json
#
# with open('tests/unit/data/tests.json', 'w') as f:
#     json.dump(response.json(), f, indent=4)

@mock.patch("requests.get", side_effect=mocked_requests_get)
@mock.patch("requests.post", side_effect=mocked_requests_post)
def test_download_manager_setup(mock_get,mock_post):

    with tempfile.TemporaryDirectory() as tmpdirname:
        _ = DownloadManager(
            user_key='use_key',
            user_secret='user_secret',
            data_dir=tmpdirname,
            native_file_dir=tmpdirname,
        )

#

@mock.patch("requests.get", side_effect=mocked_requests_get)
@mock.patch("requests.post", side_effect=mocked_requests_post)
def test_data_tailor_identify_available_datasets(mock_get,mock_post):
    """If there were a test here, there would also be a docstring here."""

    start_date = datetime.now(tz=timezone.utc) - timedelta(hours=2)
    end_date = datetime.now(tz=timezone.utc)

    with tempfile.TemporaryDirectory() as tmpdirname:
        download_manager = DownloadManager(
            user_key='user_key',
            user_secret='user_secret',
            data_dir=tmpdirname,
            native_file_dir=tmpdirname,
        )

        datasets = download_manager.identify_available_datasets(
            start_date=start_date.strftime("%Y-%m-%d-%H-%M-%S"),
            end_date=end_date.strftime("%Y-%m-%d-%H-%M-%S"),
            product_id="EO:EUM:DAT:MSG:HRSEVIRI",
        )

        assert len(datasets) > 0


@mock.patch("requests.get", side_effect=mocked_requests_get)
@mock.patch("requests.post", side_effect=mocked_requests_post)
@mock.patch("requests.patch", side_effect=mocked_requests_patch)
def test_data_tailor(mock_get,mock_post, mock_patch):
# def test_data_tailor():
    """If there were a test here, there would also be a docstring here."""

    # user_key = os.environ.get("EUMETSAT_USER_KEY")
    # user_secret = os.environ.get("EUMETSAT_USER_SECRET")

    user_key = 'user_key'
    user_secret = 'user_secret'

    start_date = datetime.now(tz=timezone.utc) - timedelta(hours=2)
    end_date = datetime.now(tz=timezone.utc)

    with tempfile.TemporaryDirectory() as tmpdirname:
        download_manager = DownloadManager(
            user_key=user_key,
            user_secret=user_secret,
            data_dir=tmpdirname,
            native_file_dir=tmpdirname,
        )

        datasets = download_manager.identify_available_datasets(
            start_date=start_date.strftime("%Y-%m-%d-%H-%M-%S"),
            end_date=end_date.strftime("%Y-%m-%d-%H-%M-%S"),
            product_id="EO:EUM:DAT:MSG:HRSEVIRI",
        )

        assert len(datasets) > 0
        # only download one dataset
        datasets = datasets[0:1]

        download_manager.download_tailored_datasets(
            datasets,
            product_id="EO:EUM:DAT:MSG:HRSEVIRI",
        )

        native_files = list(glob.glob(os.path.join(tmpdirname, "*HRSEVIRI")))
        assert len(native_files) > 0

        native_files = list(glob.glob(os.path.join(tmpdirname, "*HRSEVIRI_HRV")))
        assert len(native_files) > 0
