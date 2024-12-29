"""

This script is designed to open, process, and save to a single large Zarr satellite imagery, similar to the NWP one.

Taken from tests detailed in https://github.com/openclimatefix/ocf_datapipes/issues/132, one of the fastest methods
of reading files seems to be with 12 timestep chunks, so that's how it'll be saved.

Steps:
For each year:
1. Get all file names in order
2. Give multiprocessing workers sets of 12 filenames to open at a time
3. Load sets of 12 at a time (1 chunk)
4. Give the loaded data to the main thread
5. Write chunk to disk

"""
import json
import multiprocessing
import os
import shutil
import warnings
from argparse import ArgumentParser
from glob import glob

import dask
import numpy as np
import pandas as pd
import xarray as xr
from ocf_blosc2.ocf_blosc2 import Blosc2
from tqdm import tqdm


def read_zarrs(files, dim, transform_func=None):
    def process_one_path(path):
        # use a context manager, to ensure the file gets closed after use
        with xr.open_dataset(path) as ds:
            # transform_func should do some sort of selection or
            # aggregation
            if transform_func is not None:
                ds = transform_func(ds)
            # load all data from the transformed dataset, to ensure we can
            # use it after closing each original file
            ds.load()
            return ds

    paths = sorted(glob(files))
    datasets = [process_one_path(p) for p in paths]
    combined = xr.concat(datasets, dim)
    return combined

def try_each_zarr_and_remove_faulty_ones(files):
    for f in files:
        try:
            xr.open_dataset(f).load()
        except:
            os.remove(f)

def read_mf_zarrs(files, preprocess_func=None):
    # use a context manager, to ensure the file gets closed after use
    with xr.open_mfdataset(
        files,
        chunks="auto",  # See issue #456 for why we use "auto".
        mode="r",
        engine="zarr",
        concat_dim="time",
        consolidated=True,
        preprocess=preprocess_func,
        combine="nested",
    ) as ds:
        ds.load()
        return ds


def preprocess_function(xr_data: xr.Dataset) -> xr.Dataset:
    attrs = xr_data.attrs
    y_coords = xr_data.coords["y_geostationary"].values
    x_coords = xr_data.coords["x_geostationary"].values
    x_dataarray = xr.DataArray(
        data=np.expand_dims(xr_data.coords["x_geostationary"].values, axis=0),
        dims=["time", "x_geostationary"],
        coords=dict(time=xr_data.coords["time"].values, x_geostationary=x_coords),
    )
    y_dataarray = xr.DataArray(
        data=np.expand_dims(xr_data.coords["y_geostationary"].values, axis=0),
        dims=["time", "y_geostationary"],
        coords=dict(time=xr_data.coords["time"].values, y_geostationary=y_coords),
    )
    xr_data["x_geostationary_coordinates"] = x_dataarray
    xr_data["y_geostationary_coordinates"] = y_dataarray
    xr_data.attrs = attrs
    return xr_data


def read_hrv_timesteps_and_return(files):
    try:
        dataset = read_mf_zarrs(files, preprocess_func=preprocess_function)
        dataset = dataset.chunk(
            {
                "time": len(dataset.time.values),
                "x_geostationary": int(5548 / 4),
                "y_geostationary": int(4176 / 4),
                "variable": -1,
            }
        )
        dataset = dataset.isel(x_geostationary=slice(0, 5548))
        dataset["data"] = dataset.data.astype(np.float16)
        for v in list(dataset.coords.keys()):
            if dataset.coords[v].dtype == object:
                dataset[v].encoding.clear()

        for v in list(dataset.variables.keys()):
            if dataset[v].dtype == object:
                dataset[v].encoding.clear()
    except Exception as e:
        print(e)
        try_each_zarr_and_remove_faulty_ones(files)
        return None

    return dataset


def read_nonhrv_timesteps_and_return(files):
    try:
        dataset = read_mf_zarrs(files)
        dataset = dataset.chunk(
            {
                "time": len(dataset.time.values),
                "x_geostationary": int(3712 / 4),
                "y_geostationary": 1392,
                "variable": -1,
            }
        ).astype(np.float16)
        for v in list(dataset.coords.keys()):
            if dataset.coords[v].dtype == object:
                dataset[v].encoding.clear()

        for v in list(dataset.variables.keys()):
            if dataset[v].dtype == object:
                dataset[v].encoding.clear()
    except Exception as e:
        print(e)
        try_each_zarr_and_remove_faulty_ones(files)
        return None

    return dataset


def write_to_zarr(dataset, zarr_name, mode, chunks):
    mode_extra_kwargs = {
        "a": {"append_dim": "time"},
        "w": {
            "encoding": {
                "data": {
                    "compressor": Blosc2("zstd", clevel=5),
                },
                "time": {"units": "nanoseconds since 1970-01-01"},
            }
        },
    }
    extra_kwargs = mode_extra_kwargs[mode]
    dataset.chunk(chunks).to_zarr(
        zarr_name, compute=True, **extra_kwargs, consolidated=True, mode=mode
    )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--hrv", action="store_true")
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--x_div", type=int, default=4)
    parser.add_argument("--y_div", type=int, default=1)
    parser.add_argument("--n_channel", type=int, default=-1)
    parser.add_argument("--time_chunk", type=int, default=12)
    parser.add_argument("--search_path", type=str, default="/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v6/")
    parser.add_argument("--out_path", type=str, default="/mnt/storage_c/")
    args = parser.parse_args()

    dask.config.set(**{"array.slicing.split_large_chunks": False})
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    pool = multiprocessing.Pool(args.workers)
    years = [2017] #list(range(2023, 2013, -1))

    for year in years:
        output_name = os.path.join(args.out_path, f"{year}_{'hrv' if args.hrv else 'nonhrv'}.zarr")
        # Check if output zarr exists, which elements are already there and ignore them for appending
        dataset_time_values = None
        if os.path.exists(output_name):
            # Try opening it, if successful, then get timestamps and exclude those from the datafiles
            try:
                with xr.open_zarr(output_name) as ds:
                    dataset_time_values = ds.time.values
                    dataset_x = len(ds.x_geostationary.values)
                    dataset_y = len(ds.y_geostationary.values)
            except Exception as e:
                print(f"Failing to open {output_name} because of {e}")
        pattern = f"{year}"
        # Get all files for a month, and use that as the name for the empty one, zip up at end and download
        data_files = sorted(
            list(
                glob(
                    os.path.join(
                        args.search_path,
                        f"{'hrv_' if args.hrv else ''}{pattern}*.zarr.zip",
                    )
                )
            )
        )

        if dataset_time_values is not None:
            print("Filtering based off old datetimes")
            # Filter times here
            new_data_files = []
            regex = '%Y%m%d%H%M'
            for f in data_files:
                f_parts = f.split("/")[-1].split(".zarr")[0]
                if args.hrv:
                    f_parts = f_parts.split("hrv_")[-1]
                dtime = pd.to_datetime(f_parts, format=regex)
                if dtime not in dataset_time_values:
                    print(f"{dtime} is not in current Zarr")
                    new_data_files.append(f)
            data_files = new_data_files
        n = args.time_chunk
        data_files = [
            data_files[i * n : (i + 1) * n] for i in range((len(data_files) + n - 1) // n)
        ]
        print(len(data_files))

        # 2. Split files into sets of 12 and send to multiprocessing
        # 3. Load and combine the files
        read_function = read_hrv_timesteps_and_return if args.hrv else read_nonhrv_timesteps_and_return
        if dataset_time_values is None:
            # Only need to write new zarr if old one didn't work
            dataset = read_function(data_files[0])
            print(dataset)
            if dataset is None:
                raise ValueError("First dataset is None, failing")
            dataset_x = len(dataset.x_geostationary.values)
            dataset_y = len(dataset.y_geostationary.values)
            write_to_zarr(
                dataset,
                output_name,
                mode="w",
                chunks={
                    "time": args.time_chunk,
                    "x_geostationary": len(dataset.x_geostationary.values) // args.x_div,
                    "y_geostationary": len(dataset.y_geostationary.values) // args.y_div,
                    "variable": args.n_channel,
                },
            )
        data_files_left = data_files[1:] if dataset_time_values is None else data_files
        for dataset in tqdm(pool.imap(read_function, data_files_left)):
            if dataset is None:
                continue
            if len(dataset.x_geostationary.values) != dataset_x or len(dataset.y_geostationary.values) != dataset_y:
                print(f"Dataets X ({len(dataset.x_geostationary.values)} vs {dataset_x}) or Y ({len(dataset.y_geostationary.values)} vs {dataset_y}) mismatch, skipping")
                continue
            write_to_zarr(
                dataset,
                output_name,
                mode="a",
                chunks={
                    "time": args.time_chunk,
                    "x_geostationary": len(dataset.x_geostationary.values) // args.x_div,
                    "y_geostationary": len(dataset.y_geostationary.values) // args.y_div,
                    "variable": args.n_channel,
                },
            )
        # Combine time coords
        ds = xr.open_zarr(output_name)
        del ds["data"]
        # Need to remove these encodings to avoid chunking
        del ds.time.encoding['chunks']
        del ds.time.encoding['preferred_chunks']
        ds.to_zarr(f"{output_name.split('.zarr')[0]}_coord.zarr", consolidated=True)
        # Remove current time ones
        shutil.rmtree(f"{output_name}/time/")
        # Add new time ones
        shutil.copytree(f"{output_name.split('.zarr')[0]}_coord.zarr/time", f"{output_name}/time")

        # Now replace the part of the .zmetadata with the part of the .zmetadata from the new coord one
        with open(f"{output_name}/.zmetadata", "r") as f:
            data = json.load(f)
            with open(f"{output_name.split('.zarr')[0]}_coord.zarr/.zmetadata", "r") as f2:
                coord_data = json.load(f2)
            data["metadata"]["time/.zarray"] = coord_data["metadata"]["time/.zarray"]
        with open(f"{output_name}/.zmetadata", "w") as f:
            json.dump(data,f)
        # When this is done, we want to rewrite the time coordinate as a few,
        # large files rather than thousands of small ones (which is what happens with appending)
        # To do this, we write a dummy array, and copy over the time coordinates, and change
        # the .zmetadata chunks to be the correct size (1/4th the size of the total times usually)
        # .zmetadata is JSON file, so can open, write the new time chunk value, and resave
        # To get the right one, open the .zmetdata of the dummy one, read out that and insert into the other
