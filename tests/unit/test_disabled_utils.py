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
import pytest
from pathlib import Path

import xarray

from satip.utils import (
    load_cloudmask_to_dataarray,
    load_native_to_dataarray,
    save_dataarray_to_zarr,
)



@pytest.mark.parametrize("area", ["UK", "RSS"])
def test_load_cloudmask_to_dataarray(area):  # noqa D102
    # RSS does seem to about 45 seconds

    cloud_mask_filename = (
        os.path.realpath(os.path.dirname(__file__))
        + "/data/raw/MSG3-SEVI-MSGCLMK-0100-0100-20200601120000.000000000Z-NA.grb"
    )

    # RSS does seem to about 45 seconds
    cloudmask_dataarray = load_cloudmask_to_dataarray(
        Path(cloud_mask_filename), temp_directory=Path(os.getcwd()), area=area
    )
    assert type(cloudmask_dataarray) == xarray.DataArray


@pytest.mark.parametrize("area", ["UK", "RSS"])
def test_load_native_to_dataarray(area):  # noqa D102
    # RSS does seem to about 45 seconds

    rss_filename = (
        os.path.realpath(os.path.dirname(__file__))
        + "/data/raw/MSG3-SEVI-MSG15-0100-NA-20221220155415.490000000Z-NA.nat"
    )

    rss_dataarray, hrv_dataarray = load_native_to_dataarray(
        Path(rss_filename), temp_directory=Path(os.getcwd()), area=area
    )
    assert type(rss_dataarray) == xarray.DataArray
    assert type(hrv_dataarray) == xarray.DataArray

def test_save_dataarray_to_zarr():  # noqa D102

    rss_filename = (
        os.path.realpath(os.path.dirname(__file__))
        + "/data/raw/MSG3-SEVI-MSG15-0100-NA-20221220155415.490000000Z-NA.nat"
    )

    # The following is a bit ugly, but since we do not want to lump two tests into one
    # test function but save_dataarray_to_zarr depends on a dataarray being loaded,
    # we have to reload the dataarray here. This means that this test can theoretically
    # fail for two reasons: Either the data-loading failed, or the data-saving failed.
    rss_dataarray, _ = load_native_to_dataarray(
        Path(rss_filename), temp_directory=Path(os.getcwd()), area="UK"
    )

    zarr_path = os.path.join(os.getcwd(), "tmp.zarr")

    save_dataarray_to_zarr(
        rss_dataarray,
        zarr_path=zarr_path,
        compressor_name="bz2",
        zarr_mode="w",
    )
    assert len(list(glob.glob(zarr_path))) == 1
