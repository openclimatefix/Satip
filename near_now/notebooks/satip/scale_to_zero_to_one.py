"""Module to scale values to the range [0, 1] and check if the data is sane.

Usage Example:
  from satip.scale_to_zero_to_one import ScaleToZeroToOne
  scaler = ScaleToZeroToOne(mins_array, maxs_array, variable_order)
  scaler.fit(dataset, dims)  # Optional, if you want to set new limits based on `dataset`
  data_array = scaler.scale(data_array)
  mask = scaler.compress_masks(mask)
"""

from typing import Iterable, Union

import numpy as np
import structlog
import xarray as xr

from satip.serialize import serialize_attrs

log = structlog.stdlib.get_logger()


class ScaleToZeroToOne:
    """ScaleToZeroToOne: rescales dataarrays so all values lie in the range [0, 1]."""

    def __init__(
        self,
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
        """Initial setting for ScaleToZeroToOne class.

        Args:
            mins: Initial setting of min-values.
            maxs: Intial setting of max-values.
            variable_order: Order in which variables will appear in the compressed XArray Dataset.
        """
        self.mins = mins
        self.maxs = maxs
        self.variable_order = variable_order

    def fit(self, dataset: xr.Dataset, dims: Iterable = ("time", "y", "x")) -> object:
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

        log.debug(
            "Calculated new min and max values",
            mins=self.mins,
            maxes=self.maxs,
            variableorder=self.variable_order,
        )

        return self

    def rescale(self, dataarray: xr.DataArray) -> Union[xr.DataArray, None]:
        """
        Rescale Xarray DataArray so all values lie in the range [0, 1].

        Warning: The original `dataarray` will be modified in-place.

        Args:
            dataarray: DataArray to rescale.
                Dims MUST be named ('time', 'x_geostationary', 'y_geostationary', 'variable')!

        Returns:
            The DataArray rescaled to [0, 1]. NaNs in the original `dataarray` will still
            be present in the returned dataarray. The returned DataArray will be float32.
        """
        for attr in ["mins", "maxs"]:
            assert (
                getattr(self, attr) is not None
            ), f"{attr} must be set in initialisation or through `fit`"

        dataarray = dataarray.reindex({"variable": self.variable_order}).transpose(
            "time", "y_geostationary", "x_geostationary", "variable"
        )

        range = self.maxs - self.mins
        dataarray -= self.mins
        dataarray /= range
        dataarray = dataarray.clip(min=0, max=1)
        dataarray = dataarray.astype(np.float32)
        dataarray.attrs = serialize_attrs(dataarray.attrs)  # Must be serializable
        return dataarray

    def compress_mask(self, dataarray: xr.DataArray) -> Union[xr.DataArray, None]:
        """Compresses Cloud masks DataArrays. See compress_mask docstring."""
        dataarray = dataarray.reindex({"variable": self.variable_order})
        return compress_mask(dataarray)


def compress_mask(dataarray: xr.DataArray) -> xr.DataArray:
    """
    Compresses Cloud masks DataArrays.

    Args:
        dataarray: DataArray to compress

    Returns:
        The compressed DataArray. The returned array will be an int8 array,
        with NaNs represented as -1.
    """
    dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")
    dataarray = dataarray.round().clip(min=0, max=3)
    dataarray = dataarray.fillna(-1)
    dataarray = dataarray.astype(np.int8)
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
