from satpy import Scene
import numpy as np
import xarray as xr
import zarr

compressor_values = zarr.Blosc(cname="zstd", clevel=5)


def load_native_to_dataarry(filename: str):
    """

    Args:
        filename:

    Returns:

    """
    scene = Scene(filenames={"seviri_l1b_native": [filename]})
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
    # While we wnat to avoid resampling as much as possible, HRV is the only one different than the others, so to make it simpler, make all the same
    dataset = scene.resample().to_xarray_dataset()
    # Then put it in an XArray DataArray
    return dataset


def reproject_datasets(_, datetime_to_filepath: dict, new_coords_fp: str, new_grid_fp: str):
    reprojector = reproj.Reprojector(new_coords_fp, new_grid_fp)

    reprojected_dss = [
        (
            reprojector.reproject(filepath, reproj_library="pyresample").pipe(
                io.add_constant_coord_to_da, "time", pd.to_datetime(datetime)
            )
        )
        for datetime, filepath in datetime_to_filepath.items()
    ]

    if len(reprojected_dss) > 0:
        ds_combined_reproj = xr.concat(reprojected_dss, "time", coords="all", data_vars="all")
        return ds_combined_reproj
    else:
        return xr.Dataset()


def save_dataset_to_zarr(
    dataset: xr.Dataset,
    zarr_filename: str,
    dim_order: list = ["time", "x", "y", "variable"],
    zarr_mode: str = "a",
) -> xr.Dataset:
    dataset = dataset.transpose(*dim_order)
    dataset["time"] = get_time_as_unix(dataset)

    _, y_size, x_size, _ = dataset.shape
    # Number of timesteps, x and y size per chunk, and channels (all 12)
    chunks = (3, y_size, x_size, 12)

    ds = xr.Dataset({"stacked_eumetsat_data": dataset.chunk(chunks)})

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

    ds.to_zarr(zarr_filename, mode=zarr_mode, consolidated=True, **extra_kwargs)

    return ds
