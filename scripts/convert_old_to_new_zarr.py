"""Convert the older zarr files to newer JPEG-XL ones"""
import glob

import numpy as np
import pandas as pd
import xarray as xr


def drop_duplicate_times(data_array: xr.DataArray, class_name: str, time_dim: str) -> xr.DataArray:
    """
    Drop duplicate times in data array

    Args:
        data_array: main data
        class_name: the data source name
        time_dim: the time dimension we want to look at

    Returns: data array with no duplicated times

    """
    # If there are any duplicated init_times then drop the duplicated init_times:
    time = pd.DatetimeIndex(data_array[time_dim])
    if not time.is_unique:
        n_duplicates = time.duplicated().sum()
        data_array = data_array.drop_duplicates(dim=time_dim)

    return data_array


def drop_non_monotonic_increasing(
    data_array: xr.DataArray, class_name: str, time_dim: str
) -> xr.DataArray:
    """
    Drop non monotonically increasing time steps

    Args:
        data_array: main data
        class_name: the data source name
        time_dim: the name of the time dimension we want to check

    Returns: data array with monotonically increase time

    """
    # If any init_times are not monotonic_increasing then drop the out-of-order init_times:
    data_array = data_array.sortby("time")
    time = pd.DatetimeIndex(data_array[time_dim])
    if not time.is_monotonic_increasing:
        total_n_out_of_order_times = 0
        while not time.is_monotonic_increasing:
            # get the first set of out of order time value
            diff = np.diff(time.view(int))
            out_of_order = np.where(diff < 0)[0]
            out_of_order = time[out_of_order]

            # remove value
            data_array = data_array.drop_sel(**{time_dim: out_of_order})

            # get time vector for next while loop
            time = pd.DatetimeIndex(data_array[time_dim])

            # save how many have been removed, just for logging
            total_n_out_of_order_times += len(out_of_order)

    return data_array


def dedupe_time_coords(dataset: xr.Dataset) -> xr.Dataset:
    """
    Preprocess datasets by de-duplicating the time coordinates.

    Args:
        dataset: xr.Dataset to preprocess
        logger: logger object to write to

    Returns:
        dataset with time coords de-duped.
    """
    data_array = dataset["stacked_eumetsat_data"]
    if "stacked_eumetsat_data" == data_array.name:
        data_array.name = "data"

    # If there are any duplicated init_times then drop the duplicated time:
    data = drop_duplicate_times(data_array=data_array, class_name="Satellite", time_dim="time")

    # If any init_times are not monotonic_increasing then drop the out-of-order init_times:
    data = drop_non_monotonic_increasing(data_array=data, class_name="Satellite", time_dim="time")
    dataset = data.to_dataset(name="data")

    assert pd.DatetimeIndex(data["time"]).is_unique
    assert pd.DatetimeIndex(data["time"]).is_monotonic_increasing

    return dataset


hrv_names = list(
    glob.glob(
        "/mnt/storage_ssd_8tb/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v3/hrv_rss_eumetsat_zarr*"
    )
)
non_hrv_names = list(
    glob.glob(
        "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v2/rss_eumetsat_zarr*"
    )
)

import os

# Renamed to data
# Convert to float32
# Conver -1 to NaN
# Divide by 1023 to get 0 to 1
# Rechunk to much larger ones
from satip.utils import save_dataset_to_zarr

def replace_osgb(dataarray: xr.DataArray) -> xr.DataArray:
    osgb_x = dataarray["x_osgb"].compute()
    osgb_y = dataarray["y_osgb"].compute()
    print(osgb_y)
    del dataarray["y_osgb"]
    del dataarray["x_osgb"]
    print(dataarray)
    # Assign x_osgb and y_osgb and set some attributes
    dataarray = dataarray.assign_coords(
        x_osgb=(("y", "x"), np.float32(osgb_x)),
        y_osgb=(("y", "x"), np.float32(osgb_y)),
        )
    for name in ["x_osgb", "y_osgb"]:
        dataarray[name].attrs = {
            "units": "meter",
            "coordinate_reference_system": "OSGB",
            }

    dataarray.x_osgb.attrs["name"] = "Easting"
    dataarray.y_osgb.attrs["name"] = "Northing"
    return dataarray

def convert_to_new_format(dataset: xr.Dataset, hrv: bool = False, new_zarr_path: str = ""):
    data_array = dataset["data"]
    data_array = data_array.astype(np.float32)
    data_array = data_array.where(data_array >= -0.5)  # Negative will be NaN
    data_array /= 1023
    data_array = data_array.clip(min=0, max=1)
    data_array["time"] = data_array.coords["time"].dt.round("5 min").values
    #data_array = replace_osgb(data_array)
    print(data_array)
    for i in range(10, len(data_array["time"].values), 10):
        save_dataset_to_zarr(
            data_array.isel(time=slice(i, i + 10)),
            zarr_path=new_zarr_path,
            compressor_name="jpeg-xl",
            zarr_mode="a",
            timesteps_per_chunk=1,
            y_size_per_chunk=512,
            x_size_per_chunk=512,
        )


def convert_to_new_format_start(dataset: xr.Dataset, hrv: bool = False, new_zarr_path: str = ""):
    data_array = dataset["data"]
    data_array = data_array.astype(np.float32)
    data_array = data_array.where(data_array >= -0.5)  # Negative will be NaN
    data_array /= 1023
    data_array = data_array.clip(min=0, max=1)
    data_array["time"] = data_array.coords["time"].dt.round("5 min").values
    #data_array = replace_osgb(data_array)
    print(data_array)
    if not os.path.exists(new_zarr_path):
        save_dataset_to_zarr(
            data_array.isel(time=slice(0, 10)),
            zarr_path=new_zarr_path,
            compressor_name="jpeg-xl",
            zarr_mode="w",
            timesteps_per_chunk=1,
            y_size_per_chunk=512,
            x_size_per_chunk=512,
        )


from multiprocessing import Pool

pool = Pool(processes=8)


def fix_hrv(non_name):
    new_path = non_name.replace("v3", "v4")
    print(new_path)
    dataset = xr.open_zarr(non_name, consolidated=True)
    dataset = dedupe_time_coords(dataset)
    convert_to_new_format_start(dataset, hrv=True, new_zarr_path=new_path)


def fix_non_hrv(non_name):
    new_path = non_name.replace("v2", "v3")
    print(new_path)
    dataset = xr.open_zarr(non_name, consolidated=True)
    dataset = dedupe_time_coords(dataset)
    convert_to_new_format_start(dataset, hrv=False, new_zarr_path=new_path)


for _ in pool.imap_unordered(fix_non_hrv, non_hrv_names):
    print()

for _ in pool.imap_unordered(fix_hrv, hrv_names):
    print()



def fix_hrv_full(non_name):
    new_path = non_name.replace("v3", "v4")
    print(new_path)
    dataset = xr.open_zarr(non_name, consolidated=True)
    dataset = dedupe_time_coords(dataset)
    convert_to_new_format(dataset, hrv=True, new_zarr_path=new_path)


def fix_non_hrv_full(non_name):
    new_path = non_name.replace("v2", "v3")
    print(new_path)
    dataset = xr.open_zarr(non_name, consolidated=True)
    dataset = dedupe_time_coords(dataset)
    convert_to_new_format(dataset, hrv=False, new_zarr_path=new_path)


for _ in pool.imap_unordered(fix_hrv_full, hrv_names):
    print()

for _ in pool.imap_unordered(fix_non_hrv_full, non_hrv_names):
    print()
