import os

os.environ["SAT_API_KEY"] = "SWdEnLvOlVTVGli1An1nKJ3NcV0a"
os.environ["SAT_API_SECRET"] = "gUQe0ej7H_MqQVGF4cd7wfQWcawa"
import modal

app = modal.Stub("eumetsat-processing")

mount = modal.Mount(local_file="/home/jacob/Downloads/jxl-debs-amd64-debian-bullseye-v0.7.0/libjxl_0.7_amd64.deb", remote_dir="/")
image = modal.Image.conda().copy(mount, "/downloads").apt_install("libbrotli1").run_commands("dpkg -i /downloads/libjxl_0.7_amd64.deb").conda_install(["zarr", "s3fs", "fsspec", "xarray", "satpy[all]"]).pip_install(["satip"])


@app.function(image=image, secret=modal.Secret.from_name("eumetsat"), memory=8192, rate_limit=modal.RateLimit(per_minute=6), concurrency_limit=6)
def f(datasets):
    import glob
    import tempfile

    import numcodecs
    import numpy as np
    import pandas as pd
    import xarray as xr
    import zarr
    from satpy import Scene

    from satip.eumetsat import DownloadManager
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
            "jpeg-xl": numcodecs.Blosc("zstd"),
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
        with zarr.ZipStore(hrv_save_file, mode="w") as store:
            hrv_dataset.to_zarr(store, mode="w", consolidated=True, compute=True, **extra_kwargs)
        del hrv_dataarray
        del hrv_dataset

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
        with zarr.ZipStore(save_file, mode="w") as store:
            dataset.to_zarr(store, mode="w", consolidated=True, compute=True, **extra_kwargs)
        del dataarray
        del dataset

        # Now zip the folders and return the byte objects to the caller?
        with open(hrv_save_file, "rb") as image:
            hrv_bytes = bytearray(image.read())
            with open(save_file, "rb") as non2:
                nonhrv_bytes = bytearray(non2.read())
                return hrv_bytes, nonhrv_bytes, now_time


if __name__ == "__main__":

    import pandas as pd

    from satip.eumetsat import DownloadManager, eumetsat_filename_to_datetime

    date_range = pd.date_range(start="2023-01-01 00:00", end="2023-01-31 00:00", freq="1W")
    api_key = os.environ["SAT_API_KEY"]
    api_secret = os.environ["SAT_API_SECRET"]
    download_manager = DownloadManager(user_key=api_key, user_secret=api_secret, data_dir="./")
    for date in date_range[::-1]:
        start_date = pd.Timestamp(date) - pd.Timedelta("1W")
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
            if os.path.exists(
                os.path.join(
                    "/run/media/jacob/Windows/",
                    f"{pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}.zarr.zip",
                )
            ) and os.path.exists(
                os.path.join(
                    "/run/media/jacob/Windows/",
                    f"hrv_{pd.Timestamp(eumetsat_filename_to_datetime(dataset['id'])).round('5 min').strftime('%Y%m%d%H%M')}.zarr.zip",
                )
            ):
                print("Skipping Time")
                continue
            else:
                tmp_datasets.append(dataset)
        if len(tmp_datasets) > 0:
                with app.run():
                    try:
                        hrv, dataarray, now_time = f.map(tmp_datasets)
                        if hrv is None:
                            continue
                        save_file = os.path.join(
                            "/run/media/jacob/Windows/",
                            f"hrv_{now_time}.zarr.zip",
                        )

                        with open(save_file, "wb") as h:
                            h.write(hrv)
                        save_file = os.path.join(
                            "/run/media/jacob/Windows/",
                            f"{now_time}.zarr.zip",
                        )
                        with open(save_file, "wb") as w:
                            w.write(dataarray)
                    except Exception as e:
                        print(e)
                        raise e
                        continue
