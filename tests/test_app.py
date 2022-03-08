"""
Tests for the consumer app
"""
import glob
import os
import tempfile

from click.testing import CliRunner

from satip.app import run

runner = CliRunner()


def test_save_to_netcdf():
    user_key = os.environ.get("EUMETSAT_USER_KEY")
    user_secret = os.environ.get("EUMETSAT_USER_SECRET")
    with tempfile.TemporaryDirectory() as tmpdirname:
        response = runner.invoke(
            run, ["--api-key", user_key, "--api-secret", user_secret, "--save-dir", tmpdirname]
        )
        native_files = list(glob.glob(os.path.join(tmpdirname, "*.nat")))
        assert len(native_files) > 0
        assert os.path.exists(os.path.join(tmpdirname, "latest.nc"))
        assert os.path.exists(os.path.join(tmpdirname, "hrv_latest.nc"))
