import multiprocessing as mp

try:
   mp.set_start_method('spawn', force=True)
except RuntimeError:
   pass

import logging
import multiprocessing as mp
import os
from itertools import repeat

import dask
import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm

from satip.eumetsat import DownloadManager, eumetsat_filename_to_datetime
from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs



def func(datasets_and_tuples_and_return_data):

    import glob
    import tempfile

    import numpy as np
    import pandas as pd
    import xarray as xr
    from satpy import Scene
    import logging

    from satip.scale_to_zero_to_one import ScaleToZeroToOne
    from satip.serialize import serialize_attrs
    from satip.utils import convert_scene_to_dataarray
    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    import warnings

    warnings.filterwarnings("ignore", category=RuntimeWarning)

    process_dataset, hrv_data, non_hrv_data, return_data = datasets_and_tuples_and_return_data
    with tempfile.TemporaryDirectory() as tmpdir:
        process_dataset = [process_dataset]
        api_key = os.environ["SAT_API_KEY"]
        api_secret = os.environ["SAT_API_SECRET"]
        download_manager = DownloadManager(
            user_key=api_key, user_secret=api_secret, data_dir=tmpdir
        )
        download_manager.download_datasets(process_dataset)
        # 2. Load nat files to one Xarray Dataset
        tmp_filename = list(glob.glob(os.path.join(tmpdir, "*.nat")))
        if len(tmp_filename) == 0:
            return None, None, None
        else:
            tmp_filename = tmp_filename[0]

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
        """
        hrv_scaler = ScaleToZeroToOne(
            variable_order=["HRV"], maxs=np.array([103.90016]), mins=np.array([-1.2278595])
        )
        data_scene = Scene(filenames={"seviri_l1b_native": [tmp_filename]})
        data_scene.load(
            [
                "HRV",
            ]
        )
        hrv_dataarray: xr.DataArray = convert_scene_to_dataarray(
            data_scene, band="HRV", area="RSS", calculate_osgb=False
        )
        attrs = serialize_attrs(hrv_dataarray.attrs)
        hrv_dataarray = hrv_scaler.rescale(hrv_dataarray)
        hrv_dataarray.attrs.update(attrs)

        now_time = pd.Timestamp(hrv_dataarray["time"].values[0]).strftime("%Y%m%d%H%M")

        hrv_dataarray = hrv_dataarray.transpose(
            "time", "y_geostationary", "x_geostationary", "variable"
        )

        hrv_dataset = hrv_dataarray.to_dataset(name="data")
        y_coord_dataarray = xr.DataArray(
            data=np.expand_dims(hrv_dataarray.coords["y_geostationary"].values, 0),
            coords=dict(
                y_geostationary=hrv_dataarray.coords["y_geostationary"].values,
                time=hrv_dataarray["time"].values
            ),
            dims=["time", "y_geostationary"],
        )
        x_coord_dataarray = xr.DataArray(
            data=np.expand_dims(hrv_dataarray.coords["x_geostationary"].values, 0),
            coords=dict(
                x_geostationary=hrv_dataarray.coords["x_geostationary"].values,
                time=hrv_dataarray["time"].values
            ),
            dims=["time", "x_geostationary"],
        )
        hrv_dataset["y_geostationary_coordinates"] = y_coord_dataarray
        hrv_dataset["x_geostationary_coordinates"] = x_coord_dataarray
        """
        data_scene = Scene(filenames={"seviri_l1b_native": [tmp_filename]})
        data_scene.load(
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
            data_scene, band="IR_016", area="RSS", calculate_osgb=False
        )
        attrs = serialize_attrs(dataarray.attrs)
        dataarray = scaler.rescale(dataarray)
        dataarray.attrs.update(attrs)
        now_time = pd.Timestamp(dataarray["time"].values[0]).strftime("%Y%m%d%H%M")

        dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")

        dataset = dataarray.to_dataset(name="data")

        if return_data:
            print(f"Returning {now_time}")
            return None, dataset, now_time
        else:
            print(f"Writing {now_time}")
            # Write into the monthly Zarr file
            # Write non-HRV
            write_region(
                dataset,
                path=non_hrv_data[0],
                times=non_hrv_data[1],
                x=non_hrv_data[2],
                y=non_hrv_data[3],
                hrv=False
            )
            #write_region(
            #    hrv_dataset, path=hrv_data[0], times=hrv_data[1], x=hrv_data[2], y=hrv_data[3], hrv=True
            #)


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
                data.coords["variable"].values):  # JPEGXL only can take a single channel image at this time
            data.isel(variable=[j]).to_zarr(path, region={"time": slice(i, i + 1), "y_geostationary": slice(0, 1392),
                                                          "x_geostationary": slice(0, 3712),
                                                          "variable": slice(j, j + 1)})
        print(f"Finished non-HRV writing: {i}")
    data.close()


def create_dummy_zarr(datasets, base_path):
    hrv, non_hrv, now_time = func((datasets[0], None, None, True))
    timestamps = []
    non_hrv_path = os.path.join(
        base_path,
        pd.Timestamp(eumetsat_filename_to_datetime(datasets[0]["id"]))
        .round("5 min")
        .strftime("%Y%U")
        + ".zarr",
    )
    hrv_path = os.path.join(
        base_path,
        "hrv_"
        + pd.Timestamp(eumetsat_filename_to_datetime(datasets[0]["id"]))
        .round("5 min")
        .strftime("%Y%U")
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
    """
    hrv_dummies = dask.array.zeros(
        (len(datasets), 4176, 5568, 1), chunks=(1, 4176, 5568, 1), dtype="float32"
    )
    y_choord_dummies = dask.array.zeros(
        (len(datasets), 4176), chunks=(1, 4176), dtype="float32"
    )
    x_choord_dummies = dask.array.zeros(
        (len(datasets), 5568), chunks=(1, 5568), dtype="float32"
    )
    hrv_ds = xr.Dataset(
        data_vars=dict(
            data=(["time", "y_geostationary", "x_geostationary", "variable"], hrv_dummies),
            y_geostationary_coordinates=(["time", "y_geostationary"], y_choord_dummies),
            x_geostationary_coordinates = (["time", "x_geostationary"], x_choord_dummies),
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
    """

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

    #hrv_ds.to_zarr(hrv_path, compute=False, **extra_kwargs, consolidated=True, mode="w")
    print(f"Finished writing {non_hrv_path}, {hrv_path}")

    return (
        hrv_path, None, None, None
        #hrv_ds["time"].values,
        #hrv_ds["x_geostationary"].values,
        #hrv_ds["y_geostationary"].values,
    ), (non_hrv_path, ds["time"].values, ds["x_geostationary"].values, ds["y_geostationary"].values)


if __name__ == "__main__":


    logging.disable(logging.DEBUG)
    logging.disable(logging.INFO)

    import warnings

    warnings.filterwarnings("ignore", category=RuntimeWarning)

    date_range = pd.date_range(start="2011-01-01 00:00", end="2022-01-01 00:00", freq="4W")
    api_key = os.environ["SAT_API_KEY"]
    api_secret = os.environ["SAT_API_SECRET"]
    download_manager = DownloadManager(user_key=api_key, user_secret=api_secret, data_dir="./")
    first = True
    for date in date_range[::-1]:
        start_date = pd.Timestamp(date) - pd.Timedelta("4W")
        end_date = pd.Timestamp(date) + pd.Timedelta("1min")
        datasets = download_manager.identify_available_datasets(
            start_date=start_date.strftime("%Y-%m-%d-%H-%M-%S"),
            end_date=end_date.strftime("%Y-%m-%d-%H-%M-%S"),
        )
        print(len(datasets))
        if len(datasets) == 0:
            continue
        # tmp_datasets = datasets
        print(f"Num datasets left: {len(datasets)}")
        # Get a single example for filling in the Zarr dataset
        hrv_tuple, non_hrv_tuple = create_dummy_zarr(
            datasets, "/mnt/storage_ssd_4tb/EUMETSAT_Zarr_monthly/"
        )
        # Now map datasets to f
        pool = mp.Pool(processes=16)
        for _ in tqdm(
            pool.imap_unordered(
                func, zip(datasets, repeat(hrv_tuple), repeat(non_hrv_tuple), repeat(False))
            ),
            total=len(datasets)
        ):
            continue
