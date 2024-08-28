"""
Integration Tests for the consumer app
"""
import datetime
import glob
import os
import tempfile
import pytest

from click.testing import CliRunner
from freezegun import freeze_time

from satip.app import run

runner = CliRunner()


@freeze_time("2022-06-28 12:00:00")  # Date with RSS imagery
def test_save_to_netcdf():  # noqa 103
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:

        run(api_key=user_key,
            api_secret=user_secret,
            save_dir=tmpdirname,
            use_rescaler=False,
            start_time=datetime.datetime.utcnow().isoformat(),
            maximum_n_datasets=1)

        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0


@freeze_time("2024-08-28 12:00:00")  # Date with IODC
def test_iodc():  # noqa 103

    from satip import utils
    utils.setupLogging()

    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:

        run(api_key=user_key,
            api_secret=user_secret,
            save_dir=tmpdirname,
            save_dir_native=tmpdirname,
            use_rescaler=False,
            start_time=datetime.datetime.utcnow().isoformat(),
            maximum_n_datasets=1,
            history="15 minutes",
            use_iodc=True)

        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0


def test_save_to_netcdf_now():  # noqa 103
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")

    with tempfile.TemporaryDirectory() as tmpdirname:

        run(api_key=user_key,
            api_secret=user_secret,
            save_dir=tmpdirname,
            use_rescaler=False,
            maximum_n_datasets=1)

        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0


def test_cleanup_now():  # noqa 103
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:

        run(api_key=user_key,
            api_secret=user_secret,
            save_dir=tmpdirname
            ,use_rescaler=False,
            cleanup=True,
            maximum_n_datasets=1)

        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) == 0


@freeze_time("2022-06-22 12:00:00")  # Date with no RSS imagery
@pytest.mark.skip('This works locally but CI doesnt seem to work')
def test_save_datatailor_to_disk():  # noqa 103
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:
        response = runner.invoke(
            run,
            [
                "--api-key",
                user_key,
                "--api-secret",
                user_secret,
                "--save-dir",
                tmpdirname,
                "--use-rescaler",
                False,
                "--start-time",
                datetime.datetime.utcnow().isoformat(),
                "--maximum-n-datasets",
                1,
            ],
            catch_exceptions=False,
        )
        assert response.exit_code == 0, response.exception
        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0


@freeze_time("2022-06-28 12:00:00")  # Date with RSS imagery
def test_save_to_netcdf_rescaled():  # noqa 103
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:

        run(api_key=user_key,
            api_secret=user_secret,
            save_dir=tmpdirname,
            use_rescaler=True,
            start_time=datetime.datetime.utcnow().isoformat(),
            maximum_n_datasets=1)

        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0


def test_use_backup():  # noqa 103
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:

        run(api_key=user_key,
            api_secret=user_secret,
            save_dir=tmpdirname,
            use_rescaler=False,
            start_time=datetime.datetime.utcnow().isoformat(),
            maximum_n_datasets=1,
            use_hr_serviri=True)

        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0
