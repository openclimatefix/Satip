"""Module to compress data and check its sanity.

Class which handles compression of a XArray Dataset by forcing it to use
10-bit-int and of a cloud mask to clip values. Data completeness and serialization
are also checked.

Usage Example:
  from satip.compression import Compressor
  compressor = Compressor(bits_per_pixel, mins_array, maxs_array, variable_order)
  compressor.fit(dataset, dims)  # Optional, if you want to set new limits based on `dataset`
  data_array = compressor.compress(data_array)
  mask = compressor.compress_maks(mask)
"""

from typing import Iterable, Union

import numpy as np
import xarray as xr

from satip.serialize import serialize_attrs


class Compressor:
    """Compressor class which handles compression of dataarrays and masks."""

    def __init__(
        self,
        bits_per_pixel=10,
        mins=np.array(
            [
                -1.2278595,
                -2.5118103,
                -64.83977,
                63.404694,
                2.844452,
                199.10002,
                -17.254883,
                -26.29155,
                -1.1009827,
                -2.4184198,
                199.57048,
                198.95093,
            ]
        ),
        maxs=np.array(
            [
                103.90016,
                69.60857,
                339.15588,
                340.26526,
                317.86752,
                313.2767,
                315.99194,
                274.82297,
                93.786545,
                101.34922,
                249.91806,
                286.96323,
            ]
        ),
        variable_order=[
            "HRV",
            "IR_016",
            "IR_039",
            "IR_087",
            "IR_097",
            "IR_108",
            "IR_120",
            "IR_134",
            "VIS006",
            "VIS008",
            "WV_062",
            "WV_073",
        ],
    ):
        """Initial setting for Compressor class.

        Args:
            bits_per_pixel: integer bit-length into which XArray Datasets will be compressed.
            mins: Initial setting of min-values.
            maxs: Intial setting of max-values.
            variable_order: Order in which variables will appear in the compressed XArray Dataset.
        """

        self.bits_per_pixel = bits_per_pixel
        self.mins = mins
        self.maxs = maxs
        self.variable_order = variable_order

    def fit(self, dataset: xr.Dataset, dims: Iterable = ("time", "y", "x")) -> None:
        """
        Calculate new min and max values for the compression

        Args:
            dataset: Xarray Dataset
            dims: Dims to compute over

        """
        dims = list(dims)
        self.mins = dataset.min(dims).compute()
        self.maxs = dataset.max(dims).compute()
        self.variable_order = dataset.coords["variable"].values

        print(f"The mins are: {self.mins}")
        print(f"The maxs are: {self.maxs}")
        print(f"The variable order is: {self.variable_order}")

    def compress(self, dataarray: xr.DataArray) -> Union[xr.DataArray, None]:
        """
        Compress Xarray DataArray to use 10-bit integers

        Args:
            dataarray: DataArray to compress

        Returns:
            The compressed DataArray
        """
        for attr in ["mins", "maxs"]:
            assert (
                getattr(self, attr) is not None
            ), f"{attr} must be set in initialisation or through `fit`"

        dataarray = dataarray.reindex({"variable": self.variable_order}).transpose(
            "time", "y_geostationary", "x_geostationary", "variable"
        )

        upper_bound = (2 ** self.bits_per_pixel) - 1
        new_max = self.maxs - self.mins

        dataarray -= self.mins
        dataarray /= new_max
        dataarray *= upper_bound
        dataarray = dataarray.round().clip(min=0, max=upper_bound).astype(np.int16)
        dataarray.attrs = serialize_attrs(dataarray.attrs)  # Must be serializable

        return dataarray

    def compress_mask(self, dataarray: xr.DataArray) -> Union[xr.DataArray, None]:
        """
        Compresses Cloud masks DataArrays

        Args:
            dataarray: DataArray to compress

        Returns:
            The compressed DataArray
        """
        dataarray = dataarray.reindex({"variable": self.variable_order}).transpose(
            "time", "y_geostationary", "x_geostationary", "variable"
        )
        dataarray = dataarray.round().clip(min=0, max=3).astype(np.int16)
        dataarray.attrs = serialize_attrs(dataarray.attrs)  # Must be serializable

        return dataarray


def is_dataset_clean(dataarray: xr.DataArray) -> bool:
    """
    Checks if all the data values in a Dataset are not NaNs

    Args:
        dataarray: Xarray DataArray containing the data to check

    Returns:
        Bool of whether the dataset is clean or not
    """
    return (
        dataarray.notnull().compute().all().values and np.isfinite(dataarray).compute().all().values
    )
