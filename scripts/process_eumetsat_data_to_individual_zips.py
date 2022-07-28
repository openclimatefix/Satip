import multiprocessing as mp
import os

from tqdm import tqdm


def f(datasets):
    import glob
    import tempfile

    import numpy as np
    import pandas as pd
    import xarray as xr
    import zarr
    from satpy import Scene

    from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs
    from satip.scale_to_zero_to_one import ScaleToZeroToOne
    from satip.serialize import serialize_attrs
    from satip.utils import convert_scene_to_dataarray

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
        print("Loaded HRV")
        hrv_dataarray: xr.DataArray = convert_scene_to_dataarray(
            hrv_scene, band="HRV", area="RSS", calculate_osgb=False
        )
        attrs = serialize_attrs(hrv_dataarray.attrs)
        hrv_dataarray = hrv_scaler.rescale(hrv_dataarray)
        hrv_dataarray.attrs.update(attrs)

        now_time = pd.Timestamp(hrv_dataarray["time"].values[0]).strftime("%Y%m%d%H%M")

        # Save out
        hrv_save_file = os.path.join(tmpdir, f"hrv_{now_time}.zarr.zip")

        hrv_dataarray = hrv_dataarray.transpose(
            "time", "y_geostationary", "x_geostationary", "variable"
        )

        # Number of timesteps, x and y size per chunk, and channels (all 12)
        chunks = (
            1,
            1536,
            1536,
            1,
        )
        hrv_dataarray = hrv_dataarray.chunk(chunks)

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
                        "chunks": chunks,
                    },
                    "time": {"units": "nanoseconds since 1970-01-01"},
                }
            },
        }

        extra_kwargs = zarr_mode_to_extra_kwargs["w"]

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
        print("Loaded Non-HRV")
        dataarray: xr.DataArray = convert_scene_to_dataarray(
            scene, band="IR_016", area="RSS", calculate_osgb=False
        )
        attrs = serialize_attrs(dataarray.attrs)
        dataarray = scaler.rescale(dataarray)
        dataarray.attrs.update(attrs)

        save_file = os.path.join(tmpdir, f"{now_time}.zarr.zip")

        dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")

        # Number of timesteps, x and y size per chunk, and channels (all 12)
        chunks = (
            1,
            768,
            768,
            1,
        )
        dataarray = dataarray.chunk(chunks)

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
                        "chunks": chunks,
                    },
                    "time": {"units": "nanoseconds since 1970-01-01"},
                }
            },
        }

        extra_kwargs = zarr_mode_to_extra_kwargs["w"]

        dataset = dataarray.to_dataset(name="data")
        print("Writing HRV")
        with zarr.ZipStore(hrv_save_file, mode="w") as store:
            hrv_dataset.to_zarr(store, mode="w", consolidated=True, compute=True, **extra_kwargs)
        del hrv_dataarray
        del hrv_dataset
        print("Writing Non-HRV")
        with zarr.ZipStore(save_file, mode="w") as store:
            dataset.to_zarr(store, mode="w", consolidated=True, compute=True, **extra_kwargs)
        del dataarray
        del dataset

        # Now zip the folders and return the byte objects to the caller?
        print("Returning")
        with open(hrv_save_file, "rb") as image:
            hrv_bytes = bytearray(image.read())
            with open(save_file, "rb") as non2:
                nonhrv_bytes = bytearray(non2.read())
                return hrv_bytes, nonhrv_bytes, now_time


if __name__ == "__main__":
    import time
    from itertools import repeat

    import numpy as np
    import pandas as pd
    import zarr

    from satip.eumetsat import DownloadManager, eumetsat_filename_to_datetime
    from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs

    date_range = pd.date_range(start="2017-01-01 00:00", end="2022-06-30 00:00", freq="1D")
    api_key = os.environ["SAT_API_KEY"]
    api_secret = os.environ["SAT_API_SECRET"]
    download_manager = DownloadManager(user_key=api_key, user_secret=api_secret, data_dir="./")
    for date in date_range:
        start_date = pd.Timestamp(date) - pd.Timedelta("1D")
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
                        "/home/jacob/drive/",
                        f"{pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}.zarr.zip",
                    )
                ):
                    print(
                        f"Skipping Time {pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}"
                    )
                    continue
                if os.path.exists(
                    os.path.join(
                        "/home/jacob/drive/",
                        f"{pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}.zarr.zip",
                    )
                ):
                    print(
                        f"Skipping Time {pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}"
                    )
                    continue
            except AttributeError:
                continue
            tmp_datasets.append(dataset)
        if len(tmp_datasets) == 0:
            continue

        # Now map datasets to f
        pool = mp.Pool(processes=10)
        for hrv, dataarray, now_time in tqdm(pool.imap_unordered(f, datasets)):
            if hrv is None:
                continue
            save_file = os.path.join("/home/jacob/drive/", f"hrv_{now_time}.zarr.zip")

            with open(save_file, "wb") as h:
                h.write(hrv)
            save_file = os.path.join("/home/jacob/drive/", f"{now_time}.zarr.zip")
            with open(save_file, "wb") as w:
                w.write(dataarray)
