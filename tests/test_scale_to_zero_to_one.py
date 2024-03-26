"""Tests for scale_to_zero_to_one.py."""
import pytest

import numpy as np
import pandas as pd
import xarray as xr

from satip.scale_to_zero_to_one import ScaleToZeroToOne, is_dataset_clean


@pytest.fixture
def dataset():
    """Fixture for the dataset setup."""
    # Set dimensionality of the fake dataset:
    Nx, Ny, Nt = 2, 3, 10

    # Generate the fake four-dimensional data:
    data = np.zeros((Nx, Ny, Nt, 2))
    data[:, :, :, 0] = np.linspace(-10, 10, Nt, endpoint=True) + np.random.rand(Nx, Ny, Nt)
    data[:, :, :, 1] = np.linspace(10, -10, Nt, endpoint=True) + np.random.rand(Nx, Ny, Nt)

    # Set some random values in the middle to NaN:
    data[Nx // 2, Ny // 2, Nt // 2, :] = np.nan

    dataset = xr.DataArray(
        data=data,
        coords=dict(
            lon=(
                ["x_geostationary", "y_geostationary"],
                np.linspace(0, 1.0, Nx, endpoint=True).reshape((Nx, 1)) + np.zeros((Nx, Ny)),
            ),
            lat=(
                ["x_geostationary", "y_geostationary"],
                np.linspace(-1.0, 0.0, Ny, endpoint=True).reshape((1, Ny)) + np.zeros((Nx, Ny)),
            ),
            time=pd.date_range("2019-03-08", periods=Nt),
        ),
        dims=["x_geostationary", "y_geostationary", "time", "variable"],
        attrs=dict(
            description="Some randomly permutated lines in time and space.\
                 If you find meaning in this, please see a shrink."
        ),
    )

    yield dataset


@pytest.mark.usefixtures('dataset')
class TestScaleToZeroToOne:
    """Test class for methods of class scale_to_zero_to_one.ScaleToZeroToOne.

    We will set up a mock dataset and try the various methods in ScaleToZeroToOne,
    checking whether expected results manifest themselves.
    """

    def test_fit(self, dataset):
        scaler = ScaleToZeroToOne(
            mins=np.asarray([-5, 0]),
            maxs=np.asarray([5, 20]),
            variable_order=["wrong_var_name_one", "wrong_var_name_two"],
        )
        scaler.fit(dataset, dims=("x_geostationary", "y_geostationary", "time"))

        # Test whether the min/max-values are logged:
        assert scaler.mins.values.tolist() == dataset.min(
            ("x_geostationary", "y_geostationary", "time")
        ).compute().values.tolist()
        assert scaler.maxs.values.tolist() == dataset.max(
            ("x_geostationary", "y_geostationary", "time")
        ).compute().values.tolist()

        # Test whether the initially wrong variable names are set correctly now:
        assert scaler.variable_order.tolist() == [0, 1]

    def test_rescale(self, dataset):
        scaler = ScaleToZeroToOne().fit(dataset, dims=("x_geostationary", "y_geostationary", "time"))
        dataset = scaler.rescale(dataset)
        scaler.fit(dataset, dims=("x_geostationary", "y_geostationary", "time"))

        # Assert that all values are between zero and one:
        assert scaler.mins.values.tolist() == [0, 0]
        assert scaler.maxs.values.tolist() == [1, 1]

        # Are the NaN still in there?
        assert np.isnan(dataset).any()

    def test_compress_mask(self, dataset):
        # Generate a dataset and rescale it.
        # The result should be a dataset which still contains NaNs.
        scaler = ScaleToZeroToOne().fit(dataset, dims=("x_geostationary", "y_geostationary", "time"))
        dataset = scaler.rescale(dataset)

        # Now compress the dataset and then check if the NaNvalues have been replaced with -1:
        dataset = scaler.compress_mask(dataset)

        assert dataset.min() == -1
        assert not np.isnan(dataset).any()

        # While we are at it, let's also test the is_dataset_clean-method:
        assert is_dataset_clean(dataset)
