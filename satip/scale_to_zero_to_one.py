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
import xarray as xr

from satip.serialize import serialize_attrs


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

    def rescale(self, dataarray: xr.DataArray) -> Union[xr.DataArray, None]:
        """
        Rescale Xarray DataArray so all values lie in the range [0, 1].

        Warning: The original `dataarray` will be modified in-place.

        Args:
            dataarray: DataArray to rescale.

        Returns:
            The rescaled DataArray. NaNs in the original `dataarray` will still be NaNs
              in the returned DataArray.
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
        # JPEG-XL cannot handle NaN values, so we must encode NaNs as a different value.
        # See the docstring of encode_nans_as_floats for more details.
        dataarray = encode_nans_as_floats(dataarray)
        dataarray.attrs = serialize_attrs(dataarray.attrs)  # Must be serializable

        return dataarray

    def compress_mask(self, dataarray: xr.DataArray) -> Union[xr.DataArray, None]:
        """
        Compresses Cloud masks DataArrays

        Args:
            dataarray: DataArray to compress

        Returns:
            The compressed DataArray. The returned array will be a float array
            with values in the set {0, 85, 170, 255}.
        """
        dataarray = dataarray.reindex({"variable": self.variable_order}).transpose(
            "time", "y_geostationary", "x_geostationary", "variable"
        )
        # If we leave the values in the range [0, 3], JPEG-XL will
        # think the image is a very dark image, and apply much more agressive compression
        # (because it assumes the human eye doesn't care about details in the shadows.)
        # So we stretch the values to fill up the range of uint8 values:
        #
        # NaNs are represented as the value 0
        # 0 in the original mask becomes 64
        # 1 becomes 128
        # 2 becomes 192
        # 3 becomes 255

        dataarray = dataarray.round().clip(min=0, max=3)
        dataarray += 1
        dataarray *= 64
        dataarray -= 1  # Because uint8 goes up to 255, not 256.
        dataarray = dataarray.fillna(0)
        dataarray = dataarray.astype(np.uint8)
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


def encode_nans_as_floats(dataarray: xr.DataArray) -> xr.DataArray:
    """Encode NaNs as the value 0.025. Encode all other values in the range [0.075, 1].

    JPEG-XL does not understand "NaN" values. JPEG-XL only understands floating
    point values in the range [0, 1]. So we must encode NaN values
    as real values in the range [0, 1].

    After JPEG-XL compression, there is slight "ringing" around the edges
    of regions with filled with a constant number. In experiments, it appears
    that the values at the inner edges of a "NaN region" vary in the range
    [0.0227, 0.0280]. But, to be safe, we use a nice wide margin: We don't set
    the value of "NaNs" to be 0.00 because the ringing would cause the values
    to drop below zero, which is illegal for JPEG-XL images.

    After decompression, reconstruct regions of NaNs using "image < 0.05" to find NaNs.

    See this comment for more info:
    https://github.com/openclimatefix/Satip/issues/67#issuecomment-1036456502

    Args:
        dataarray (xr.DataArray): The input DataArray. All values must already
            be in the range [0, 1]. The original dataarray is modified in place.

    Returns:
        xr.DataArray: The returned DataArray. "Real" values will be shifted to
            the range [0.075, 1]. NaNs will be encoded as 0.025.
    """
    LOWER_BOUND_FOR_REAL_PIXELS = 0.075
    NAN_VALUE = 0.025

    assert issubclass(
        dataarray.dtype.type, np.floating
    ), f"dataarray.dtype must be floating point not {dataarray.dtype}!"
    dataarray = dataarray.clip(min=0, max=1)

    # Shift all the "real" values up to the range [0.075, 1]
    dataarray /= 1 + LOWER_BOUND_FOR_REAL_PIXELS
    dataarray += LOWER_BOUND_FOR_REAL_PIXELS
    dataarray = dataarray.fillna(NAN_VALUE)
    return dataarray
