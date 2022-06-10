import os
import asyncio
import modal.aio
import pandas as pd
import zarr
import time
from pathlib import Path
import numpy as np
from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs
from satip.eumetsat import DownloadManager
from satip.eumetsat import eumetsat_filename_to_datetime
app = modal.aio.AioApp(image=modal.Conda().conda_install(["zarr", "s3fs", "fsspec", "xarray", "satpy[all]"]).pip_install(["satip"]))

def decompress(full_bzip_filename, temp_pth) -> str:
    """
    Decompresses .bz2 file and returns the non-compressed filename

    Args:
        full_bzip_filename: Full compressed filename
        temp_pth: Temporary path to save the native file

    Returns:
        The full native filename to the decompressed file
    """
    import subprocess
    base_bzip_filename = os.path.basename(full_bzip_filename)
    base_nat_filename = os.path.splitext(base_bzip_filename)[0]
    full_nat_filename = os.path.join(temp_pth, base_nat_filename)
    if os.path.exists(full_nat_filename):
        os.remove(full_nat_filename)
    with open(full_nat_filename, "wb") as nat_file_handler:
        process = subprocess.run(
            ["pbzip2", "--decompress", "--keep", "--stdout", full_bzip_filename],
            stdout=nat_file_handler,
        )
    process.check_returncode()
    return full_nat_filename

@app.function()
async def f(compressed_bytearray_and_filename):
    import tempfile
    from pathlib import Path
    import bz2
    import pandas as pd
    import glob
    import numpy as np
    import zarr
    import time
    from satip.jpeg_xl_float_with_nans import JpegXlFloatWithNaNs
    from satip.scale_to_zero_to_one import ScaleToZeroToOne
    from satip.serialize import serialize_attrs
    from satip.eumetsat import DownloadManager
    from satip.utils import convert_scene_to_dataarray
    import xarray as xr
    from satpy import Scene
    start = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        compressed_bytearray, filename = compressed_bytearray_and_filename
        # Write compressed bytearray to disk uncompressed
        with open(os.path.join(tmpdir, filename), 'wb') as file:
            file.write(bz2.decompress(compressed_bytearray))
            print(f"Finished writing {filename}")
        del compressed_bytearray
        # 2. Load nat files to one Xarray Dataset
        f = os.path.join(tmpdir, filename)

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
        hrv_save_file = os.path.join(
            tmpdir, f"hrv_{now_time}.zarr.zip"
        )

        hrv_dataarray = hrv_dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")

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
        with zarr.ZipStore(hrv_save_file, mode="w") as store:
            hrv_dataset.to_zarr(store, mode="w", consolidated=True, compute=True, **extra_kwargs)
            print("Finished writing HRV to file")
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


        save_file = os.path.join(
            tmpdir, f"{now_time}.zarr.zip"
        )

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
            print("Finished writing non-HRV to file")
        del dataarray
        del dataset

        # Now zip the folders and return the byte objects to the caller?
        with open(hrv_save_file, "rb") as image:
            hrv_bytes = bytearray(image.read())
            with open(save_file, "rb") as non2:
                nonhrv_bytes = bytearray(non2.read())
                end = time.time()
                print(f"Returning {now_time} in {end - start} seconds")
                return hrv_bytes, nonhrv_bytes, now_time

async def main():
    directory = "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/native/"
    year_directories = sorted(os.listdir(directory), reverse=True)
    print(year_directories)
    dirs = []
    for year in year_directories:
        if not os.path.isdir(os.path.join(directory, year)):
            continue
        if str(year) not in ["2016", "2017", "2018", "2019", "2020"]:
            continue
        month_directories = sorted(os.listdir(os.path.join(directory, year)), reverse=True)
        for month in month_directories:
            if not os.path.isdir(os.path.join(directory, year, month)):
                continue
            month_directory = os.path.join(directory, year.split("/")[0], month.split("/")[0])
            dirs.append(month_directory)

    for month in dirs:
        compressed_native_files = sorted(list(Path(month).rglob("*.bz2")))
        print(len(compressed_native_files))
        if len(compressed_native_files) == 0:
            continue
        new_compressed_files = []
        for filepath in compressed_native_files:
            if os.path.exists(os.path.join("/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/",f"{pd.Timestamp(eumetsat_filename_to_datetime(filepath.name)).round('5 min').strftime('%Y%m%d%H%M')}.zarr.zip")):
                print("Skipping Time")
                continue
            else:
                new_compressed_files.append(filepath)
        if len(new_compressed_files) == 0:
            continue
        byted_datas = []
        for compressed_file in new_compressed_files:
            print(compressed_file)
            with open(compressed_file, "rb") as image:
                data_bytes = bytearray(image.read())
                filename = str(compressed_file.name).replace(".bz2", "")
                print(filename)
                byted_datas.append((data_bytes, filename))
            if len(byted_datas) >= 10:
                try:
                    async with app.run():
                        results = await asyncio.gather(*[f(data_pack) for data_pack in byted_datas], return_exceptions=True)
                        cleaned_results = []
                        for r in results:
                            try:
                                hrv, dataarray, now_time = r
                                cleaned_results.append((hrv, dataarray, now_time))
                            except:
                                continue
                        for hrv, dataarray, now_time in cleaned_results:
                            if hrv is None:
                                continue
                            save_file = os.path.join(
                                "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/", f"hrv_{now_time}.zarr.zip"
                            )

                            with open(save_file, "wb") as h:
                                h.write(hrv)
                            save_file = os.path.join(
                                "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/", f"{now_time}.zarr.zip"
                            )
                            with open(save_file, "wb") as w:
                                w.write(dataarray)
                        byted_datas = []
                except:
                    async with app.run():
                        results = await asyncio.gather(*[f(data_pack) for data_pack in byted_datas], return_exceptions=True)
                        cleaned_results = []
                        for r in results:
                            try:
                                hrv, dataarray, now_time = r
                                cleaned_results.append((hrv, dataarray, now_time))
                            except:
                                continue
                        for hrv, dataarray, now_time in cleaned_results:
                            if hrv is None:
                                continue
                            save_file = os.path.join(
                                "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/", f"hrv_{now_time}.zarr.zip"
                            )

                            with open(save_file, "wb") as h:
                                h.write(hrv)
                            save_file = os.path.join(
                                "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/", f"{now_time}.zarr.zip"
                            )
                            with open(save_file, "wb") as w:
                                w.write(dataarray)
                        byted_datas = []
        try:
            # To handle all the extras
            async with app.run():
                results = await asyncio.gather(*[f(data_pack) for data_pack in byted_datas], return_exceptions=True)
                cleaned_results = []
                for r in results:
                    try:
                        hrv, dataarray, now_time = r
                        cleaned_results.append((hrv, dataarray, now_time))
                    except:
                        continue
                for hrv, dataarray, now_time in cleaned_results:
                    if hrv is None:
                        continue
                    save_file = os.path.join(
                        "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/", f"hrv_{now_time}.zarr.zip"
                    )

                    with open(save_file, "wb") as h:
                        h.write(hrv)
                    save_file = os.path.join(
                        "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/", f"{now_time}.zarr.zip"
                    )
                    with open(save_file, "wb") as w:
                        w.write(dataarray)
        except:
            # To handle all the extras
            async with app.run():
                results = await asyncio.gather(*[f(data_pack) for data_pack in byted_datas], return_exceptions=True)
                cleaned_results = []
                for r in results:
                    try:
                        hrv, dataarray, now_time = r
                        cleaned_results.append((hrv, dataarray, now_time))
                    except:
                        continue
                for hrv, dataarray, now_time in cleaned_results:
                    if hrv is None:
                        continue
                    save_file = os.path.join(
                        "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/", f"hrv_{now_time}.zarr.zip"
                    )

                    with open(save_file, "wb") as h:
                        h.write(hrv)
                    save_file = os.path.join(
                        "/mnt/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v5/", f"{now_time}.zarr.zip"
                    )
                    with open(save_file, "wb") as w:
                        w.write(dataarray)

if __name__ == "__main__":
    asyncio.run(main())
