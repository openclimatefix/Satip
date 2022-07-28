import glob
import logging
import multiprocessing as mp
import os
import tempfile
from itertools import repeat

import dask
import numpy as np
import pandas as pd
import xarray as xr
from satpy import Scene
from tqdm import tqdm

from satip.eumetsat import DownloadManager, eumetsat_filename_to_datetime
from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs
from satip.scale_to_zero_to_one import ScaleToZeroToOne
from satip.serialize import serialize_attrs
from satip.utils import convert_scene_to_dataarray

logging.disable(logging.DEBUG)
logging.disable(logging.INFO)

import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


def func(datasets_and_tuples_and_return_data):
    datasets, hrv_tuple, non_hrv_tuple, return_data = datasets_and_tuples_and_return_data
    with tempfile.TemporaryDirectory() as tmpdir:
        datasets = [datasets]
        api_key = os.environ["SAT_API_KEY"]
        api_secret = os.environ["SAT_API_SECRET"]
        download_manager = DownloadManager(
            user_key=api_key, user_secret=api_secret, data_dir=tmpdir
        )
        download_manager.download_datasets(datasets)
        # 2. Load nat files to one Xarray Dataset
        f = list(glob.glob(os.path.join(tmpdir, "*.nat")))
        if len(f) == 0:
            return None, None, None
        else:
            f = f[0]

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

        now_time = pd.Timestamp(hrv_dataarray["time"].values[0]).strftime("%Y%m%d%H%M")

        hrv_dataarray = hrv_dataarray.transpose(
            "time", "y_geostationary", "x_geostationary", "variable"
        )

        hrv_dataset = hrv_dataarray.to_dataset(name="data")
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
        # print("Loaded Non-HRV")
        dataarray: xr.DataArray = convert_scene_to_dataarray(
            scene, band="IR_016", area="RSS", calculate_osgb=False
        )
        attrs = serialize_attrs(dataarray.attrs)
        dataarray = scaler.rescale(dataarray)
        dataarray.attrs.update(attrs)

        dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")

        dataset = dataarray.to_dataset(name="data")

        if return_data:
            return hrv_dataset, dataset, now_time
        else:
            # Write into the monthly Zarr file
            # Write non-HRV
            write_region(
                dataset,
                path=non_hrv_tuple[0],
                times=non_hrv_tuple[1],
                x=non_hrv_tuple[2],
                y=non_hrv_tuple[3],
            )
            write_region(
                hrv_dataset, path=hrv_tuple[0], times=hrv_tuple[1], x=hrv_tuple[2], y=hrv_tuple[3]
            )


def write_region(data, path, x, y, times):
    if len(data.coords["x_geostationary"].values) == 5568:  # Flip should work?
        print("Flipping X")
        data = data.isel(x_geostationary=slice(None, None, -1))
    elif len(data.coords["x_geostationary"].values) == 5570:  # Need to trim off 2 pixels
        data = data.isel(x_geostationary=slice(0, 5568))

    # Quick checks on coordinates
    assert np.isclose(data.coords["x_geostationary"][:10].values, x[:10]).all()
    assert np.isclose(data.coords["y_geostationary"][:10].values, y[:10]).all()
    assert np.isclose(data.coords["y_geostationary"][-10:].values, y[-10:]).all()
    assert np.isclose(data.coords["x_geostationary"][-10:].values, x[-10:]).all()

    # Write to where index of the time is, so get i from there
    # times is the times values for the thing, so get the index here
    i = np.argmin(np.abs(times - data["time"][0]))
    data.to_zarr(
        path,
        region={
            "time": slice(i, i + 1),
            "y_geostationary": slice(0, 4176),
            "x_geostationary": slice(0, len(data.coords["x_geostationary"].values)),
            "variable": slice(0, 1),
        },
    )
    data.close()


def create_dummy_zarr(datasets, base_path):
    hrv, non_hrv, now_time = func((datasets[0], None, None, True))
    timestamps = []
    non_hrv_path = os.path.join(
        base_path,
        pd.Timestamp(eumetsat_filename_to_datetime(datasets[0]["id"]))
        .round("5 min")
        .strftime("%Y%m")
        + ".zarr",
    )
    hrv_path = os.path.join(
        base_path,
        "hrv_"
        + pd.Timestamp(eumetsat_filename_to_datetime(datasets[0]["id"]))
        .round("5 min")
        .strftime("%Y%m")
        + ".zarr",
    )
    for dataset in datasets:
        timestamps.append(
            pd.Timestamp(eumetsat_filename_to_datetime(dataset["id"]))
            .round("5 min")
            .to_datetime64()
        )

    dummies = dask.array.zeros(
        (len(datasets), 1392, 3712, 11), chunks=(1, 1392, 3712, 1), dtype="float32"
    )
    ds = xr.Dataset(
        data_vars=dict(data=(["time", "y_geostationary", "x_geostationary", "variable"], dummies)),
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
    hrv_dummies = dask.array.zeros(
        (len(datasets), 4176, 5568, 1), chunks=(1, 4176, 5568, 1), dtype="float32"
    )
    hrv_ds = xr.Dataset(
        data_vars=dict(
            data=(["time", "y_geostationary", "x_geostationary", "variable"], hrv_dummies)
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

    ds.to_zarr(non_hrv_path, compute=False, **extra_kwargs, consolidated=True)
    hrv_ds.to_zarr(hrv_path, compute=False, **extra_kwargs, consolidated=True)

    return (
        hrv_path,
        hrv_ds["time"].values,
        hrv_ds["x_geostationary"].values,
        hrv_ds["y_geostationary"].values,
    ), (non_hrv_path, ds["time"].values, ds["x_geostationary"].values, ds["y_geostationary"].values)


if __name__ == "__main__":

    date_range = pd.date_range(start="2011-01-01 00:00", end="2019-01-01 00:00", freq="1M")
    api_key = os.environ["SAT_API_KEY"]
    api_secret = os.environ["SAT_API_SECRET"]
    download_manager = DownloadManager(user_key=api_key, user_secret=api_secret, data_dir="./")
    first = True
    for date in date_range[::-1]:
        start_date = pd.Timestamp(date) - pd.Timedelta("1M")
        end_date = pd.Timestamp(date) + pd.Timedelta("1min")
        datasets = download_manager.identify_available_datasets(
            start_date=start_date.strftime("%Y-%m-%d-%H-%M-%S"),
            end_date=end_date.strftime("%Y-%m-%d-%H-%M-%S"),
        )
        print(len(datasets))
        if len(datasets) == 0:
            continue
        tmp_datasets = []
        for dataset in datasets:
            try:
                if os.path.exists(
                    os.path.join(
                        "/mnt/storage_ssd_4tb/EUMETSAT_Zarr/",
                        f"{pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}.zarr.zip",
                    )
                ):
                    print(
                        f"Skipping Time {pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}"
                    )
                    continue
                if os.path.exists(
                    os.path.join(
                        "/home/jacob/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v6/",
                        f"{pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}.zarr.zip",
                    )
                ):
                    print(
                        f"Skipping Time {pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}"
                    )
                    continue
            except AttributeError as e:
                print(e)
                continue
            tmp_datasets.append(dataset)
        if len(tmp_datasets) == 0:
            continue
        # tmp_datasets = datasets
        print(f"Num datasets left: {len(tmp_datasets)}")
        # Get a single example for filling in the Zarr dataset
        hrv_tuple, non_hrv_tuple = create_dummy_zarr(
            datasets, "/mnt/storage_ssd_4tb/EUMETSAT_Zarr/"
        )
        # Now map datasets to f
        pool = mp.Pool(processes=48)
        first = False
        for _ in tqdm(
            pool.imap_unordered(
                func, zip(datasets, repeat(hrv_tuple), repeat(non_hrv_tuple), repeat(False))
            ),
            total=len(datasets),
        ):
            continue
