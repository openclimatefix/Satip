"""
Tests for the consumer app
"""
import glob
import os
import tempfile

from click.testing import CliRunner

from satip.app import run

runner = CliRunner() 


def test_save_to_netcdf():  # noqa 103
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:
        runner.invoke(
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
            ],
        )
        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0


def test_save_to_netcdf_rescaled():  # noqa 103
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:
        runner.invoke(
            run,
            [
                "--api-key",
                user_key,
                "--api-secret",
                user_secret,
                "--save-dir",
                tmpdirname,
                "--use-rescaler",
                True,
            ],
        )
        native_files = list(glob.glob(os.path.join(tmpdirname, "*.zarr.zip")))
        assert len(native_files) > 0
