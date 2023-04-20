import ocf_blosc2
import xarray as xr
import satpy
from satpy import Scene
from satip.eumetsat import DownloadManager
from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs
from satip.scale_to_zero_to_one import ScaleToZeroToOne
from satip.serialize import serialize_attrs
from satip.utils import convert_scene_to_dataarray
import os
import numpy as np
import pandas as pd
import glob
import shutil
import json


def download_data(last_zarr_time):
    api_key = os.environ["SAT_API_KEY"]
    api_secret = os.environ["SAT_API_SECRET"]
    download_manager = DownloadManager(user_key=api_key, user_secret=api_secret, data_dir="./")
    start_date = pd.Timestamp.utcnow()
    date_range = pd.date_range(start=start_date.strftime("%Y-%m-%d-%H-%M-%S"),
                               end=pd.Timestamp(last_zarr_time, tz="UTC").strftime("%Y-%m-%d-%H-%M-%S"),
                               freq="1D")
    for date in date_range:
        start_date = pd.Timestamp(date) - pd.Timedelta("1min")
        end_date = pd.Timestamp(date) + pd.Timedelta("1min")
        datasets = download_manager.identify_available_datasets(
            start_date=start_date.strftime("%Y-%m-%d-%H-%M-%S"),
            end_date=end_date.strftime("%Y-%m-%d-%H-%M-%S"),
        )
        download_manager.download_datasets(datasets)

    # Get native files in order
    native_files = list(glob.glob("./native_files/*"))
    native_files.sort()
    return native_files


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


def open_and_scale_data_hrv(zarr_times, f):
    hrv_scaler = ScaleToZeroToOne(
        variable_order=["HRV"], maxs=np.array([103.90016]), mins=np.array([-1.2278595])
    )

    hrv_scene = Scene(filenames={"seviri_l1b_native": [f]})
    hrv_scene.load(
        [
            "HRV",
        ]
    )
    hrv_dataarray: xr.DataArray = convert_scene_to_dataarray(
        hrv_scene, band="HRV", area="RSS", calculate_osgb=False
    )
    attrs = serialize_attrs(hrv_dataarray.attrs)
    hrv_dataarray = hrv_scaler.rescale(hrv_dataarray)
    hrv_dataarray.attrs.update(attrs)
    hrv_dataarray = hrv_dataarray.transpose(
        "time", "y_geostationary", "x_geostationary", "variable"
    )
    hrv_dataset = hrv_dataarray.to_dataset(name="data")
    hrv_dataset["data"] = hrv_dataset["data"].astype(np.float16)

    if hrv_dataset.time.values[0] in zarr_times:
        print("Skipping")
        return None

    return hrv_dataset


def open_and_scale_data_nonhrv(zarr_times, f):
    """Zarr path is the path to the zarr file to extend, f is native file to open and scale"""
    scaler = ScaleToZeroToOne(
        mins=np.array(
            [
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
    )

    scene = Scene(filenames={"seviri_l1b_native": [f]})
    scene.load(
        [
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
    dataarray: xr.DataArray = convert_scene_to_dataarray(
        scene, band="IR_016", area="RSS", calculate_osgb=False
    )
    attrs = serialize_attrs(dataarray.attrs)
    dataarray = scaler.rescale(dataarray)
    dataarray.attrs.update(attrs)
    dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")
    dataset = dataarray.to_dataset(name="data")
    dataset["data"] = dataset.data.astype(np.float16)

    if dataset.time.values[0] in zarr_times:
        print("Skipping")
        return None

    return dataset


def write_to_zarr(dataset, zarr_name, mode, chunks):
    mode_extra_kwargs = {
        "a": {"append_dim": "time"},
    }
    extra_kwargs = mode_extra_kwargs[mode]
    dataset.chunk(chunks).to_zarr(
        zarr_name, compute=True, **extra_kwargs, consolidated=True, mode=mode
    )


def rewrite_zarr_times(output_name):
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
        json.dump(data, f)


if __name__ == "__main__":
    zarr_path = "/mnt/disks/data/2023_hrv.zarr"
    non_zarr_path = "/mnt/disks/data/2023_nonhrv.zarr"
    zarr_times = xr.open_zarr(non_zarr_path).sortby("time").time.values
    hrv_zarr_times = xr.open_zarr(zarr_path).sortby("time").time.values
    last_zarr_time = zarr_times[-1]
    native_files = download_data(last_zarr_time)
    datasets = []
    hrv_datasets = []
    for f in native_files:
        dataset = open_and_scale_data_nonhrv(zarr_times, f)
        if dataset is not None:
            datasets.append(dataset)
        if len(datasets) == 12:
            write_to_zarr(xr.concat(datasets, dim="time"), non_zarr_path, "a", chunks={"time": 12})
            write_to_zarr(
                xr.concat(hrv_datasets, dim="time"), zarr_path, "a", chunks={"time": 12}
            )
            datasets = []
    for f in native_files:
        dataset = open_and_scale_data_hrv(hrv_zarr_times, f)
        if dataset is not None:
            datasets = preprocess_function(dataset)
            hrv_datasets.append(dataset)
        if len(hrv_datasets) == 12:
            write_to_zarr(
                xr.concat(hrv_datasets, dim="time"), zarr_path, "a", chunks={"time": 12}
            )
            hrv_datasets = []
    rewrite_zarr_times(non_zarr_path)
    rewrite_zarr_times(zarr_path)
