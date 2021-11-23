#!/usr/bin/env python
# coding: utf-8

import dask
import xarray as xr

ZARR_PATH = "/mnt/storage_ssd_8tb/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v2/eumetsat_*.zarr"

DIMS = ["time", "x", "y"]


def main():
    ds_from_zarr = xr.open_mfdataset(
        ZARR_PATH,
        mode="r",
        engine="zarr",
        chunks="auto",
        parallel=True,
        concat_dim="time",
        combine="nested",
        preprocess=lambda dataset: dataset.drop_vars("acq_time", errors="ignore"),
    )
    data = ds_from_zarr["stacked_eumetsat_data"]
    stats = xr.Dataset(
        dict(
            mean=data.mean(dim=DIMS),
            std=data.std(dim=DIMS),
            min=data.min(dim=DIMS),
            max=data.max(dim=DIMS),
        )
    )
    print("Computing...")
    stats = dask.compute(stats)
    print(stats)
    for stat_name in ["mean", "std", "min", "max"]:
        print(stat_name, stats[stat_name].values)


if __name__ == "__main__":
    main()
