"""
Tests for the consumer app
"""
import datetime
import glob
import os
import tempfile
import pytest
from unittest import mock

from click.testing import CliRunner
from freezegun import freeze_time

from satip.app import app

from .conftest import mocked_requests_get, mocked_requests_post, mocked_requests_patch


runner = CliRunner()


@freeze_time("2020-06-01 12:00:00")
@mock.patch("requests.get", side_effect=mocked_requests_get)
@mock.patch("requests.post", side_effect=mocked_requests_post)
@mock.patch("requests.patch", side_effect=mocked_requests_patch)
def test_app(m, n, o, zip_file, caplog):  # noqa 103
    # user_key = 'os.environ.get("EUMETSAT_USER_KEY")'
    # user_secret = 'os.environ.get("EUMETSAT_USER_SECRET")'
    with tempfile.TemporaryDirectory() as tmpdirname:

        app(
            api_key="api_key",
            api_secret="user_secret",
            save_dir=tmpdirname,
            use_rescaler=False,
            start_time="2020-06-01 13:00:00",
            maximum_n_datasets=1,
            save_s3=False,
        )

        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0


@freeze_time("2020-06-01 12:00:00")
@mock.patch("requests.get", side_effect=mocked_requests_get)
@mock.patch("requests.post", side_effect=mocked_requests_post)
@mock.patch("requests.patch", side_effect=mocked_requests_patch)
def test_app_clean_up(m, n, o, zip_file, caplog):  # noqa 103
    # user_key = 'os.environ.get("EUMETSAT_USER_KEY")'
    # user_secret = 'os.environ.get("EUMETSAT_USER_SECRET")'
    with tempfile.TemporaryDirectory() as tmpdirname:

        app(
            api_key="api_key",
            api_secret="user_secret",
            save_dir=tmpdirname,
            use_rescaler=False,
            start_time="2020-06-01 13:00:00",
            maximum_n_datasets=1,
            save_s3=False,
            cleanup=True
        )

        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) == 0
