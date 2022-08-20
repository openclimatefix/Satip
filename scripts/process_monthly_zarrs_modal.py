import logging
from itertools import repeat

import dask
import modal
import numpy as np
import pandas as pd
import xarray as xr

from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs

stub = modal.Stub()

volume = modal.SharedVolume().persist("zarr-cache")

CACHE_DIR = "/cache"

stub["empty_app"] = (
    modal.Conda()
    .conda_install(["zarr", "s3fs", "fsspec", "xarray", "dask", "pandas", "numpy"])
    .pip_install(["satip"])
)

stub["app"] = (
    modal.Conda()
    .conda_install(["zarr", "s3fs", "fsspec", "xarray", "dask", "pandas", "numpy"])
    .pip_install(["satip"])
)

stub["download_cache"] = modal.Conda()


def save_and_load_bytes(dataset_bytes, hrv_dataset_bytes):
    with open("hrv.zarr.zip", "wb") as h:
        h.write(hrv_dataset_bytes)
    with open("nonhrv.zarr.zip", "wb") as h:
        h.write(dataset_bytes)

    del dataset_bytes
    del hrv_dataset_bytes

    # Load and write to disk now
    dataset: xr.Dataset = xr.open_zarr("nonhrv.zarr.zip")

    hrv_dataset: xr.Dataset = xr.open_zarr("hrv.zarr.zip")
    y_coord_dataarray = xr.DataArray(
        data=np.expand_dims(hrv_dataset.coords["y_geostationary"].values, 0),
        coords=dict(
            y_geostationary=hrv_dataset.coords["y_geostationary"].values,
            time=hrv_dataset["time"].values,
        ),
        dims=["time", "y_geostationary"],
    )
    x_coord_dataarray = xr.DataArray(
        data=np.expand_dims(hrv_dataset.coords["x_geostationary"].values, 0),
        coords=dict(
            x_geostationary=hrv_dataset.coords["x_geostationary"].values,
            time=hrv_dataset["time"].values,
        ),
        dims=["time", "x_geostationary"],
    )
    hrv_dataset["y_geostationary_coordinates"] = y_coord_dataarray
    hrv_dataset["x_geostationary_coordinates"] = x_coord_dataarray

    return hrv_dataset, dataset


@stub.function(image=stub["download_cache"], shared_volumes={CACHE_DIR: volume})
def download_cache(hrv_data, non_hrv_data):
    import shutil

    shutil.make_archive(hrv_data[0] + ".zip", "zip", hrv_data[0])
    shutil.make_archive(non_hrv_data[0] + ".zip", "zip", non_hrv_data[0])
    # Now zip the folders and return the byte objects to the caller?
    with open(hrv_data[0] + ".zip", "rb") as image:
        hrv_bytes = bytearray(image.read())
        with open(non_hrv_data[0] + ".zip", "rb") as non2:
            nonhrv_bytes = bytearray(non2.read())
            return hrv_bytes, nonhrv_bytes


@stub.function(
    image=stub["app"],
    secret=modal.ref("eumetsat"),
    shared_volumes={CACHE_DIR: volume},
    memory=8192,
    concurrency_limit=16,
)
def func(dataset_bytes, hrv_dataset_bytes, hrv_data, non_hrv_data):
    import logging

    import dask
    import numpy as np
    import pandas as pd
    import xarray as xr

    from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs

    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    import warnings

    warnings.filterwarnings("ignore", category=RuntimeWarning)

    # Write the bytes to disk before opening them here
    hrv_dataset, dataset = save_and_load_bytes(dataset_bytes, hrv_dataset_bytes)

    # Write into the monthly Zarr file
    # Write non-HRV
    write_region(
        dataset,
        path=non_hrv_data[0],
        times=non_hrv_data[1],
        x=non_hrv_data[2],
        y=non_hrv_data[3],
        hrv=False,
    )

    write_region(
        hrv_dataset, path=hrv_data[0], times=hrv_data[1], x=hrv_data[2], y=hrv_data[3], hrv=True
    )


def write_region(data, path, x, y, times, hrv=False):
    if hrv:
        if len(data.coords["x_geostationary"].values) == 5570:  # Need to trim off 2 pixels
            data = data.isel(x_geostationary=slice(0, 5568))
    else:
        try:
            assert np.isclose(data.coords["x_geostationary"][:10].values, x[:10], atol=1e-1).all()
            assert np.isclose(data.coords["x_geostationary"][-10:].values, x[-10:], atol=1e-1).all()
        except:
            data = data.isel(x_geostationary=slice(None, None, -1))
            assert np.isclose(data.coords["x_geostationary"][:10].values, x[:10], atol=1e-1).all()
            assert np.isclose(data.coords["x_geostationary"][-10:].values, x[-10:], atol=1e-1).all()
        try:
            assert np.isclose(data.coords["y_geostationary"][:10].values, y[:10], atol=1e-1).all()
            assert np.isclose(data.coords["y_geostationary"][-10:].values, y[-10:], atol=1e-1).all()
        except:
            data = data.isel(y_geostationary=slice(None, None, -1))
            assert np.isclose(data.coords["y_geostationary"][:10].values, y[:10], atol=1e-1).all()
            assert np.isclose(data.coords["y_geostationary"][-10:].values, y[-10:], atol=1e-1).all()

    # Quick checks on coordinates
    # Write to where index of the time is, so get i from there
    # times is the times values for the thing, so get the index here
    i = np.argmin(np.abs(times - data["time"].values[0]))
    if hrv:
        data.to_zarr(
            path,
            region={
                "time": slice(i, i + 1),
                "y_geostationary": slice(0, 4176),
                "x_geostationary": slice(0, 5568),
                "variable": slice(0, 1),
            },
        )
        print(f"Finished HRV writing: {i}")
    else:
        for j, variable in enumerate(
            data.coords["variable"].values
        ):  # JPEGXL only can take a single channel image at this time
            data.isel(variable=[j]).to_zarr(
                path,
                region={
                    "time": slice(i, i + 1),
                    "y_geostationary": slice(0, 1392),
                    "x_geostationary": slice(0, 3712),
                    "variable": slice(j, j + 1),
                },
            )
        print(f"Finished non-HRV writing: {i}")
    data.close()


@stub.function(image=stub["empty_app"], shared_volumes={CACHE_DIR: volume})
def create_dummy_zarr(hrv_bytes, data_bytes, hrv_files, data_files):
    import os

    import dask
    import numpy as np
    import pandas as pd
    import xarray as xr
    import zarr

    from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs

    hrv, non_hrv = save_and_load_bytes(data_bytes, hrv_bytes)
    timestamps = []
    non_hrv_path = os.path.join(
        CACHE_DIR,
        data_files[0].split("/")[-1].split(".zarr")[0] + "_collated_4_6" + ".zarr",
    )
    hrv_path = os.path.join(
        CACHE_DIR,
        "hrv_" + hrv_files[0].split("/")[-1].split(".zarr")[0] + "_collated_4_6" + ".zarr",
    )
    for dataset in data_files:
        date = dataset.split("/")[-1].split(".zarr")[0]
        timestamps.append(
            pd.Timestamp(
                year=int(date[:4]),
                month=int(date[4:6]),
                day=int(date[6:8]),
                hour=int(date[8:10]),
                minute=int(date[10:12]),
            ).to_datetime64()
        )

    dummies = dask.array.zeros(
        (len(data_files), 1392, 3712, 11),
        chunks=(1, int(1392 / 2), int(3712 / 4), 1),
        dtype="float32",
    )
    y_chord_dummies = dask.array.zeros((len(data_files), 1392), chunks=(1, 1392), dtype="float32")
    x_chord_dummies = dask.array.zeros((len(data_files), 3712), chunks=(1, 3712), dtype="float32")
    ds = xr.Dataset(
        data_vars=dict(
            data=(["time", "y_geostationary", "x_geostationary", "variable"], dummies),
            y_geostationary_coordinates=(["time", "y_geostationary"], y_chord_dummies),
            x_geostationary_coordinates=(["time", "x_geostationary"], x_chord_dummies),
        ),
        attrs=non_hrv["data"].attrs,
        coords=dict(
            x_geostationary=non_hrv.coords["x_geostationary"],
            y_geostationary=non_hrv.coords["y_geostationary"],
            variable=non_hrv.coords["variable"],
            time=timestamps,
        ),
    )
    # ds = xr.Dataset({"data": ("x_geostationary", dummies_x, "y_geostationary", dummies_y, "time", dummies_y, "variable", dummies_v)})
    # ds.attrs = first_data["data"].attrs
    print(ds)
    timestamps = []
    for dataset in hrv_files:
        date = dataset.split("/")[-1].split(".zarr")[0].split("hrv_")[-1]
        timestamps.append(
            pd.Timestamp(
                year=int(date[:4]),
                month=int(date[4:6]),
                day=int(date[6:8]),
                hour=int(date[8:10]),
                minute=int(date[10:12]),
            ).to_datetime64()
        )

    hrv_dummies = dask.array.zeros(
        (len(hrv_files), 4176, 5568, 1),
        chunks=(1, int(4176 / 4), int(5568 / 4), 1),
        dtype="float32",
    )
    y_choord_dummies = dask.array.zeros((len(hrv_files), 4176), chunks=(1, 4176), dtype="float32")
    x_choord_dummies = dask.array.zeros((len(hrv_files), 5568), chunks=(1, 5568), dtype="float32")
    hrv_ds = xr.Dataset(
        data_vars=dict(
            data=(["time", "y_geostationary", "x_geostationary", "variable"], hrv_dummies),
            y_geostationary_coordinates=(["time", "y_geostationary"], y_choord_dummies),
            x_geostationary_coordinates=(["time", "x_geostationary"], x_choord_dummies),
        ),
        attrs=hrv["data"].attrs,
        coords=dict(
            x_geostationary=hrv.coords["x_geostationary"][
                :5568
            ],  # Some HRV files are 2 pixels smaller than rest, this just trims off 2 pixels, which should be okay?
            y_geostationary=hrv.coords["y_geostationary"],
            variable=hrv.coords["variable"],
            time=timestamps,
        ),
    )
    print(hrv_ds)

    compression_algos = {
        "jpeg-xl": JpegXlFloatWithNaNs(lossless=False, distance=0.4, effort=8),
    }
    compression_algo = compression_algos["jpeg-xl"]

    zarr_mode_to_extra_kwargs = {
        "a": {"append_dim": "time"},
        "w": {
            "encoding": {
                "data": {
                    "compressor": compression_algo,
                },
                "time": {"units": "nanoseconds since 1970-01-01"},
            }
        },
    }

    extra_kwargs = zarr_mode_to_extra_kwargs["w"]

    ds.to_zarr(non_hrv_path, compute=False, **extra_kwargs, consolidated=True, mode="w")

    hrv_zarr_mode_to_extra_kwargs = {
        "a": {"append_dim": "time"},
        "w": {
            "encoding": {
                "data": {
                    "compressor": compression_algo,
                },
                "time": {"units": "nanoseconds since 1970-01-01"},
            }
        },
    }
    extra_kwargs = hrv_zarr_mode_to_extra_kwargs["w"]

    hrv_ds.to_zarr(hrv_path, compute=False, **extra_kwargs, consolidated=True, mode="w")
    print(f"Finished writing {non_hrv_path}, {hrv_path}")

    return (
        hrv_path,
        hrv_ds["time"].values,
        hrv_ds["x_geostationary"].values,
        hrv_ds["y_geostationary"].values,
    ), (non_hrv_path, ds["time"].values, ds["x_geostationary"].values, ds["y_geostationary"].values)


def load_bytes(paths):
    for path in paths:
        with open(path, "rb") as image:
            yield bytearray(image.read())


if __name__ == "__main__":
    import glob
    import os

    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    import warnings

    warnings.filterwarnings("ignore", category=RuntimeWarning)
    # Get all files for a month, and use that as the name for the empty one, zip up at end and download
    data_files = sorted(
        list(glob.glob(os.path.join("/run/media/jacob/SSD2/modal/", "202106*.zarr.zip")))
    )
    print(len(data_files))
    hrv_data_files = sorted(
        list(glob.glob(os.path.join("/run/media/jacob/SSD2/modal/", "hrv_202106*.zarr.zip")))
    )
    print(len(data_files))
    # Do it per 5 days for testing
    with stub.run():
        with open(hrv_data_files[0], "rb") as image:
            tmp_hrv_bytes = bytearray(image.read())
        with open(data_files[0], "rb") as image:
            tmp_data_bytes = bytearray(image.read())
        # Get a single example for filling in the Zarr dataset
        hrv_tuple, non_hrv_tuple = create_dummy_zarr(
            tmp_hrv_bytes, tmp_data_bytes, hrv_data_files, data_files
        )

        # Now map datasets to f
        for _ in func.starmap(
            zip(
                load_bytes(data_files),
                load_bytes(hrv_data_files),
                repeat(hrv_tuple),
                repeat(non_hrv_tuple),
            )
        ):
            continue

        # Now download back to disk
        hrv, non_hrv = download_cache(hrv_data=hrv_tuple, non_hrv_data=non_hrv_tuple)
        with open(f"hrv_202106.zarr.zip", "wb") as h:
            h.write(hrv)
        with open(f"202106.zarr.zip", "wb") as h:
            h.write(hrv)
