"""Pipeline for downloading, processing, and saving archival satellite data.

Consolidates the old cli_downloader, backfill_hrv and backfill_nonhrv scripts.
"""
import argparse
import dataclasses
import datetime as dt
import logging
import multiprocessing
import os
import subprocess
import sys
from typing import Literal

import diskcache as dc
import numpy as np
import pandas as pd
import xarray as xr
from ocf_blosc2 import Blosc2
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from satip.scale_to_zero_to_one import ScaleToZeroToOne
from satip.serialize import serialize_attrs
from satip.utils import convert_scene_to_dataarray

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger(__name__)


@dataclasses.dataclass
class Config:
    region: str
    cadence: str
    product_id: str
    native_path: str
    zarr_path: dict[str, str]

CONFIGS: dict[str, Config] = {
    "iodc": Config(
        region="india",
        cadence="15min",
        product_id="EO:EUM:DAT:MSG:HRSEVIRI-IODC",
        native_path="/mnt/disks/sat/native_files_india/",
        zarr_path={
            "hrv": "/mnt/disks/sat/%Y_hrv_iodc.zarr",
            "nonhrv": "/mnt/disks/sat/%Y_nonhrv_iodc.zarr",
        },
    ),
    "severi": Config(
        region="europe",
        cadence="5min",
        product_id="EO:EUM:DAT:MSG:MSG15-RSS",
        native_path="/mnt/disks/sat/native_files/",
        zarr_path={
            "hrv": "/mnt/disks/sat/%Y_hrv.zarr",
            "nonhrv": "/mnt/disks/sat/%Y_nonhrv.zarr",
        },
    ),
    # Optional
    "odegree": Config(
        region="europe, africa",
        cadence="15min",
        product_id="EO:EUM:DAT:MSG:HRSEVIRI",
        native_path="/mnt/disks/sat/native_files_odegree/",
        zarr_path={
            "hrv": "/mnt/disks/sat/%Y_hrv_odegree.zarr",
            "nonhrv": "/mnt/disks/sat/%Y_nonhrv_odegree.zarr",
        },
    ),
}

@dataclasses.dataclass
class Channel:
    minimum: float
    maximum: float
    variable: str

# Approximate minimum and maximum pixel values per channel, for normalization
# * Caclulated by Jacob via the min and max of a snapshot of the data
CHANNELS: dict[str, list[Channel]] = {
    # Non-HRV is 11 channels of different filters
    "nonhrv": [
        Channel(-2.5118103, 69.60857, "IR_016"),
        Channel(-64.83977, 339.15588, "IR_039"),
        Channel(63.404694, 340.26526, "IR_087"),
        Channel(2.844452, 317.86752, "IR_097"),
        Channel(199.10002, 313.2767, "IR_108"),
        Channel(-17.254883, 315.99194, "IR_120"),
        Channel(-26.29155, 274.82297, "IR_134"),
        Channel(-1.1009827, 93.786545, "VIS006"),
        Channel(-2.4184198, 101.34922, "VIS008"),
        Channel(199.57048, 249.91806, "WV_062"),
        Channel(198.95093, 286.96323, "WV_073"),
    ],
    # HRV is one greyscale wideband filter channel
    "hrv": [
        Channel(-1.2278595, 103.90016, "HRV"),
    ],
}

parser = argparse.ArgumentParser(
    prog="EUMETSTAT Pipeline",
    description="Downloads and processes data from EUMETSTAT",
)
parser.add_argument(
    'sat',
    help="Which satellite to download data from",
    type=str,
    choices=list(CONFIGS.keys()),
)
parser.add_argument(
    "--start_date",
    help="Date to download from (YYYY-MM-DD)",
    type=dt.date.fromisoformat,
    required=True,
)
parser.add_argument(
    "--end_date",
    help="Date to download to (YYYY-MM-DD)",
    type=dt.date.fromisoformat,
    required=False,
    default=str(dt.datetime.utcnow().date()),
)

def download_scans(
        sat_config: Config,
        scan_times: list[pd.Timestamp],
    ) -> list[pd.Timestamp]:
    """Download satellite scans for a given config over the given scan times.

    Returns:
        List of scan times that failed to download.
    """
    failed_scan_times: list[pd.Timestamp] = []

    # Get credentials from environment
    consumer_key: str = os.environ["EUMETSAT_CONSUMER_KEY"]
    consumer_secret: str = os.environ["EUMETSAT_CONSUMER_SECRET"]

    # Create progressbar
    pbar = tqdm(
        total=len(scan_times),
        position=0 if scan_times[0] < scan_times[-1] else 1,
        desc="forward" if scan_times[0] < scan_times[-1] else "backward"
    )

    for i, scan_time in enumerate(scan_times):
        # Authenticate
        # * Generates a new access token with short expiry
        process = subprocess.run(
            [
                "eumdac",
                "--set-credentials",
                consumer_key,
                consumer_secret,
                "\n"
            ],
            capture_output=True,
            text=True,
        )
        if process.returncode != 0:
            log.warn(f"Unable to authenticate with eumdac: {process.stdout} {process.stderr}")
            failed_scan_times.append(scan_time)
            continue

        # Download
        window_start: pd.Timestamp = scan_time - pd.Timedelta(sat_config.cadence)
        window_end: pd.Timestamp = scan_time + pd.Timedelta(sat_config.cadence)
        process = subprocess.run(
            [
                "eumdac",
                "download",
                "-c", sat_config.product_id,
                "-s", window_start.tz_localize(None).strftime("%Y-%m-%dT%H:%M:%S"),
                "-e", window_end.tz_localize(None).strftime("%Y-%m-%dT%H:%M:%S"),
                "-o", sat_config.native_path,
                "--entry",
                "*.nat",
                "-y"
            ],
            capture_output=True,
            text=True,
        )
        if process.returncode != 0:
            log.debug(f"Failed to download scans for scan_time {scan_time}")
            failed_scan_times.append(scan_time)

        pbar.update(1)

    return failed_scan_times

def process_scans(
        sat_config: Config,
        start: dt.date,
        end: dt.date,
        dstype: Literal["hrv", "nonhrv"],
    ) -> str:

    # Check zarr file exists for the year
    zarr_path = start.strftime(sat_config.zarr_path[dstype])
    if os.path.exists(zarr_path):
        zarr_times = xr.open_zarr(zarr_path).sortby("time").time.values
        last_zarr_time = zarr_times[-1]
    else:
        # Set dummy values for times already in zarr
        last_zarr_time = dt.datetime(1970, 1, 1)
        zarr_times = [last_zarr_time, last_zarr_time]

    # Get native files in order
    native_files = list(glob.glob(f"{sat_config.native_path}*/*.nat"))
    log.info(f"Found {len(native_files)} native files at {sat_config.native_path}")
    native_files.sort()

    # Create progressbar
    pbar = tqdm(
        total=len(native_files),
        position=0 if dstype == "hrv" else 1,
        desc=f"{dstype}",
    )

    # Convert native files to xarray datasets
    # * Append to the yearly zarr in hourly chunks
    datasets: list[xr.Dataset] = []
    for f in native_files:
        try:
            dataset: xr.Dataset | None = _open_and_scale_data(zarr_times, f, dstype)
        except Exception as e:
            log.error(f"Exception: {e}")
            continue
        if dataset is not None:
            dataset = _preprocess_function(dataset)
            datasets.append(dataset)
        # Append to zarrs in hourly chunks (12 sets of 5 minute datasets)
        # * This is so zarr doesn't complain about mismatching chunk sizes
        if len(datasets) == 12:
            mode = "w"
            if os.path.exists(zarr_path):
                mode = "a"
            write_to_zarr(
                xr.concat(datasets, dim="time"),
                zarr_path,
                mode,
                chunks={"time": 12,}
            )
            datasets = []

        pbar.update(1)

    # Consolidate zarr metadata
    _rewrite_zarr_times(zarr_path)

    return dstype

def _open_and_scale_data(
        zarr_times: list[dt.datetime],
        f: str,
        dstype: Literal["hrv", "nonhrv"],
    ) -> xr.Dataset | None:
    """Opens a raw file and converts it to a normalised xarray dataset."""
    # Create a scaler according to the channel
    scaler = ScaleToZeroToOne(
        variable_order=[c.variable for c in CHANNELS[dstype]],
        maxs=np.array([c.maximum for c in CHANNELS[dstype]]),
        mins=np.array([c.minimum for c in CHANNELS[dstype]]),
    )
    # The reader is the same for each satellite as the sensor is the same
    # * Hence "severi" in all cases
    scene = Scene(filenames={"severi_l1b_native": [f]})
    scene.load([c.variable for c in CHANNELS[dstype]])
    da: xr.DataArray = convert_scene_to_dataarray(
        scene, band=CHANNELS[dstype][0].variable, area="RSS", calculate_osgb=False,
    )

    # Rescale the data, update the attributes, save as dataset
    attrs = serialize_attrs(da.attrs)
    da = scaler.rescale(da)
    da.attrs.update(attrs)
    da = da.transpose("time", "y_geostationary", "x_geostationary", "variable")
    ds: xr.Dataset = da.to_dataset(name="data")
    ds["data"] = ds.data.astype(np.float16)

    if dataset.time.values[0] in zarr_times:
        log.debug(f"Skipping: {dataset.time.values[0]}")
        return None

    return ds

def _preprocess_function(xr_data: xr.Dataset) -> xr.Dataset:
    """Updates the coordinates for the given dataset."""
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


def _write_to_zarr(dataset, zarr_name, mode, chunks):
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
    dataset.isel(x_geostationary=slice(0,5548)).chunk(chunks).to_zarr(
        zarr_name, compute=True, **extra_kwargs, consolidated=True, mode=mode
    )


def _rewrite_zarr_times(output_name):
    # Combine time coords
    ds = xr.open_zarr(output_name)

	# Prevent numcodecs string error
	# See https://github.com/pydata/xarray/issues/3476#issuecomment-1205346130
    for v in list(ds.coords.keys()):
        if ds.coords[v].dtype == object:
            ds[v].encoding.clear()

    for v in list(ds.variables.keys()):
        if ds[v].dtype == object:
            ds[v].encoding.clear()

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
    # Prevent logs interfering with progressbar
    logging_redirect_tqdm(loggers=[log])

    # Get running args
    args = parser.parse_args()
    prog_start = dt.datetime.utcnow()
    log.info(f"{str(prog_start)}: Running with args: {args}")

    # Create a reusable cache
    cache = dc.Cache('tmp')

    # Get config for desired satellite
    sat_config = CONFIGS[args.sat]

    # Get start and end times for run
    start: dt.date = args.start_date
    end: dt.date = args.end_date
    scan_times: list[pd.Timestamp] = pd.date_range(start=start, end=end, freq=sat_config.cadence).tolist()

    # Get average runtime from cache
    secs_per_scan = cache.get('secs_per_scan', default=65)
    expected_runtime = pd.Timedelta(secs_per_scan * len(scan_times), 'seconds')
    log.info(f"Downloading {len(scan_times)} scans. Expected runtime: {str(expected_runtime)}")

    # Perform data download passes
    # * Each pass has two simultaneous forward and backward download streams
    for pass_num in [0, 1]:
        pool = multiprocessing.Pool()
        log.info(f"Performing pass {pass_num}")
        results = pool.starmap(
                download_scans,
                [
                    (sat_config, scan_times),
                    (sat_config, list(reversed(scan_times))),
                ],
        )
        pool.close()
        pool.join()
        for result in results:
            log.info(f"Completed download with {len(result)} failed scan times.")


    # Calculate the new average time per timestamp
    runtime: dt.timedelta = dt.datetime.utcnow() - prog_start
    new_average_secs_per_scan: int = int((secs_per_scan + (runtime.total_seconds() / len(scan_times))) / 2)
    cache.set('secs_per_scan', new_average_secs_per_scan)
    log.info(f"Completed download for args: {args} in {str(runtime)} (avg {new_average_secs_per_scan} secs per scan)")

    # Process the HRV and non-HRV data
    pool = multiprocessing.Pool()
    results = pool.starmap(
        process_scans,
        [
            (sat_config, start, end, "hrv"),
            (sat_config, start, end, "nonhrv"),
        ]
    )
    pool.close()
    pool.join()
    for result in results:
        log.info(f"Processed {result} data")

    pool


"""
Jacob's old script!

last_zarr_time = pd.Timestamp("2024-01-01T00:00:00.000000000")
#start_zarr_time = pd.Timestamp("2024-01-01T00:00:00.000000000")
start_date = (
    pd.Timestamp.utcnow().tz_convert("UTC").to_pydatetime().replace(tzinfo=None)
)
start_zarr_time = pd.Timestamp(start_date).to_pydatetime().replace(tzinfo=None)
last_zarr_time = pd.Timestamp(last_zarr_time).to_pydatetime().replace(tzinfo=None)
start_str = last_zarr_time.strftime("%Y-%m-%d")
end_str = start_zarr_time.strftime("%Y-%m-%d")
print(start_str)
print(end_str)
date_range = pd.date_range(start=start_str, end=end_str, freq="5min")
print(date_range)
for date in date_range:
    start_date = pd.Timestamp(date) - pd.Timedelta("5min")
    end_date = pd.Timestamp(date) + pd.Timedelta("5min")
    process = subprocess.run(
        [
            "eumdac",
            "--set-credentials",
            "SWdEnLvOlVTVGli1An1nKJ3NcV0a",
            "gUQe0ej7H_MqQVGF4cd7wfQWcawa",
            "\n"
        ]
    )
    end_date_time = end_date.tz_localize(None).strftime("%Y-%m-%dT%H:%M:%S")
    start_date_time = start_date.tz_localize(None).strftime("%Y-%m-%dT%H:%M:%S")

    print(start_date_time)
    print(end_date_time)
    process = subprocess.run(
        [
            "eumdac",
            "download",
            "-c",
            "EO:EUM:DAT:MSG:MSG15-RSS",
            "-s",
            f"{end_date_time}",
            "-e",
            f"{end_date_time}",
            "-o",
            "/mnt/disks/sat/native_files/",
            "--entry",
            "*.nat",
            "-y"
        ]
    )
"""
