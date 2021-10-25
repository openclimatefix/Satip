from satpy import Scene
import xarray as xr
import zarr
from satip.utils import decompress

compressor_values = zarr.Blosc(cname="zstd", clevel=5)


def load_native_to_dataarry(filename: str, temp_directory: str) -> xr.Dataset:
    """

    Args:
        filename:

    Returns:

    """

    decompressed_filename: str = decompress(filename, temp_directory)

    scene = Scene(filenames={"seviri_l1b_native": [decompressed_filename]})
    scene.load(
        [
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
        ]
    )
    # While we wnat to avoid resampling as much as possible,
    # HRV is the only one different than the others, so to make it simpler, make all the same
    dataset = scene.resample().to_xarray_dataset()
    print(dataset)
    return dataset


# xr.concat(reprojected_dss, "time", coords="all", data_vars="all")


def save_dataset_to_zarr(
    dataset: xr.Dataset,
    zarr_filename: str,
    dim_order: list = ["time", "x", "y", "variable"],
    zarr_mode: str = "a",
    timesteps_per_chunk: int = 3,
    y_size_per_chunk: int = 256,
    x_size_per_chunk: int = 256,
) -> xr.Dataset:
    dataset = dataset.transpose(*dim_order)

    # Number of timesteps, x and y size per chunk, and channels (all 12)
    chunks = {
        "time": timesteps_per_chunk,
        "y": y_size_per_chunk,
        "x": x_size_per_chunk,
        "variable": 12,
    }

    dataset = xr.Dataset({"stacked_eumetsat_data": dataset.chunk(chunks)})

    zarr_mode_to_extra_kwargs = {
        "a": {"append_dim": "time"},
        "w": {
            "encoding": {
                "stacked_eumetsat_data": {"compressor": compressor_values, "chunks": chunks}
            }
        },
    }

    assert zarr_mode in ["a", "w"], "`zarr_mode` must be one of: `a`, `w`"
    extra_kwargs = zarr_mode_to_extra_kwargs[zarr_mode]

    dataset.to_zarr(zarr_filename, mode=zarr_mode, consolidated=True, **extra_kwargs)

    return dataset
