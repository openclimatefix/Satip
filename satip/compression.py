import xarray as xr
import numpy as np


class Compressor:
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

        self.bits_per_pixel = bits_per_pixel
        self.mins = mins
        self.maxs = maxs
        self.variable_order = variable_order

    def fit(self, dataset: xr.Dataset, dims: list = ["time", "y", "x"]) -> None:
        """
        Calculate new min and max values for the compression

        Args:
            dataset: Xarray Dataset
            dims: Dims to compute over

        """
        self.mins = dataset.min(dims).compute()
        self.maxs = dataset.max(dims).compute()
        self.variable_order = dataset.coords["variable"].values

        print(f"The mins are: {self.mins}")
        print(f"The maxs are: {self.maxs}")
        print(f"The variable order is: {self.variable_order}")

    def compress(self, dataset: xr.Dataset) -> xr.Dataset:
        """
        Compress Xarray Dataset to use 10-bit integers

        Args:
            dataset:

        Returns:

        """
        da_meta = dataset.attrs

        for attr in ["mins", "maxs"]:
            assert (
                getattr(self, attr) is not None
            ), f"{attr} must be set in initialisation or through `fit`"

        dataset = dataset.reindex({"variable": self.variable_order}).transpose(
            "time", "y", "x", "variable"
        )

        upper_bound = (2 ** self.bits_per_pixel) - 1
        new_max = self.maxs - self.mins

        dataset -= self.mins
        dataset /= new_max
        dataset *= upper_bound

        dataset = dataset.round().astype(np.int16)

        dataset.attrs = {"meta": str(da_meta)}  # Must be serializable

        return dataset