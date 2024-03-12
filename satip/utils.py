"""Utilities module to handle data and logging.

Collection of helper functions and utilities around
- data loading/saving
- data conversion
- data sanitation
- setting up a logger
- datetime string formatting
"""

import datetime
import gc
import glob
import os
import secrets
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path
from typing import Any, Tuple
from zipfile import ZipFile

import fsspec
import numcodecs
import numpy as np
import pandas as pd
import psutil
import structlog
import xarray as xr
import zarr
from ocf_blosc2 import Blosc2
from satpy import Scene

from satip.geospatial import GEOGRAPHIC_BOUNDS, lat_lon_to_osgb
from satip.scale_to_zero_to_one import ScaleToZeroToOne, compress_mask
from satip.serialize import serialize_attrs

LATEST_DIR_NAME = "latest"
log = structlog.get_logger()

warnings.filterwarnings("ignore", message="divide by zero encountered in true_divide")
warnings.filterwarnings("ignore", message="invalid value encountered in sin")
warnings.filterwarnings("ignore", message="invalid value encountered in cos")
warnings.filterwarnings("ignore", message="invalid value encountered in double_scalars")
warnings.filterwarnings("ignore", message="invalid value encountered in true_divide")
warnings.filterwarnings(
    "ignore",
    message=(
        "You will likely lose important projection information when converting "
        "to a PROJ string from another format. See: https://proj.org/faq.html"
        "#what-is-the-best-format-for-describing-coordinate-reference-systems"
    ),
)

def setupLogging() -> None:
    """Instantiate the structlog package to produce JSON logs."""

    # Add required processors and formatters to structlog
    structlog.configure(
        processors=[
            structlog.processors.EventRenamer("message", replace_by="_event"),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ],
            ),
            structlog.processors.dict_tracebacks,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
    )


def format_dt_str(datetime_string):
    """Helper function to get a consistently formatted string."""
    return pd.to_datetime(datetime_string).strftime("%Y-%m-%dT%H:%M:%SZ")


def decompress(full_bzip_filename: Path, temp_pth: Path) -> str:
    """
    Decompresses .bz2 file and returns the non-compressed filename

    Args:
        full_bzip_filename: Full compressed filename
        temp_pth: Temporary path to save the native file

    Returns:
        The full native filename to the decompressed file
    """
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


def load_native_to_dataarray(
    filename: Path, temp_directory: Path, area: str, calculate_osgb: bool = True
) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Load compressed native files into an Xarray dataset

    Resampling to the same grid for the HRV channel,
     and replacing small chunks of NaNs with interpolated values, and add a time coordinate

    Args:
        filename: The filename of the compressed native file to load
        temp_directory: Temporary directory to store the decompressed files
        area: Name of the geographic area to use, such as 'UK'
        calculate_osgb: Whether to calculate OSGB x and y coordinates,
                        only needed for first data array

    Returns:
        Returns Xarray DataArray if script worked, else returns None
    """
    hrv_scaler = ScaleToZeroToOne(
        variable_order=["HRV"], maxs=np.array([103.90016]), mins=np.array([-1.2278595])
    )
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
    if filename.suffix == ".bz2":
        try:
            # IF decompression fails, pass
            decompressed_filename: str = decompress(filename, temp_directory)
            decompressed_file = True
        except subprocess.CalledProcessError:
            return None, None
    else:
        decompressed_filename = str(filename)
        decompressed_file = False
    scene = Scene(filenames={"seviri_l1b_native": [decompressed_filename]})
    hrv_scene = Scene(filenames={"seviri_l1b_native": [decompressed_filename]})
    hrv_scene.load(
        [
            "HRV",
        ]
    )
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
    # HRV covers a smaller portion of the disk than other bands, so use that as the bounds
    # Selected bounds empirically for have no NaN values from off disk image,
    # and are covering the UK + a bit
    dataarray: xr.DataArray = convert_scene_to_dataarray(
        scene, band="IR_016", area=area, calculate_osgb=calculate_osgb
    )
    hrv_dataarray: xr.DataArray = convert_scene_to_dataarray(
        hrv_scene, band="HRV", area=area, calculate_osgb=calculate_osgb
    )
    if decompressed_file:
        # Delete file off disk, but only if we decompressed it first, so still have a copy
        os.remove(decompressed_filename)

    # Compress and return
    dataarray = scaler.rescale(dataarray)
    hrv_dataarray = hrv_scaler.rescale(hrv_dataarray)
    return dataarray, hrv_dataarray


# TODO: temp_directory is unused and has no effect. But for the sake of interface consistency
# with load_native_to_dataset, can also stay.
def load_cloudmask_to_dataarray(
    filename: Path, temp_directory: Path, area: str, calculate_osgb: bool = True
) -> xr.DataArray:
    """
    Load cloud mask files into an Xarray dataset

    Replacing small chunks of NaNs with interpolated values, and add a time coordinate

    Args:
        filename: The filename of the GRIB file to load
        temp_directory: Temporary directory to store the decompressed files
        area: Name of the geographic area to use, such as 'UK'
        calculate_osgb: Whether to calculate OSGB x and y coordinates,
                        only needed for first data array

    Returns:
        Returns Xarray DataArray if script worked, else returns None
    """
    scene = Scene(filenames={"seviri_l2_grib": [filename]})
    scene.load(
        [
            "cloud_mask",
        ]
    )
    try:
        # Selected bounds empirically that have no NaN values from off disk image,
        # and are covering the UK + a bit
        dataarray: xr.DataArray = convert_scene_to_dataarray(
            scene, band="cloud_mask", area=area, calculate_osgb=calculate_osgb
        )
        return compress_mask(dataarray)
    except Exception:
        return None


def convert_scene_to_dataarray(
    scene: Scene, band: str, area: str, calculate_osgb: bool = True
) -> xr.DataArray:
    """
    Convertes a Scene with satellite data into a data array.

    Args:
        scene: The satpy.Scene containing the satellite data
        band: The name of the band
        area: Name of the geographic area to use, such as 'UK'
        calculate_osgb: Whether to calculate OSGB x and y coordinates,
                        only needed for first data array

    Returns:
        Returns Xarray DataArray
    """
    if area not in GEOGRAPHIC_BOUNDS:
        raise ValueError(f"`area` must be one of {GEOGRAPHIC_BOUNDS.keys()}, not '{area}'")
    log.debug("Starting scene conversion", memory=get_memory())
    if area != "RSS":
        try:
            scene = scene.crop(ll_bbox=GEOGRAPHIC_BOUNDS[area])
        except NotImplementedError:
            # 15 minutely data by default doesn't work for some reason, have to resample it
            scene = scene.resample("msg_seviri_rss_1km" if band == "HRV" else "msg_seviri_rss_3km")
            log.debug("Finished resample", memory=get_memory())
            scene = scene.crop(ll_bbox=GEOGRAPHIC_BOUNDS[area])
    log.debug("Finished crop", memory=get_memory())
    # Remove acq time from all bands because it is not useful, and can actually
    # get in the way of combining multiple Zarr datasets.
    data_attrs = {}
    for channel in scene.wishlist:
        scene[channel] = scene[channel].drop_vars("acq_time", errors="ignore")
        for attr in scene[channel].attrs:
            new_name = channel["name"] + "_" + attr
            data_attrs[new_name] = scene[channel].attrs[attr]
    dataset: xr.Dataset = scene.to_xarray_dataset()
    dataarray = dataset.to_array()
    log.debug("Converted to dataarray", memory=get_memory())

    # Lat and Lon are the same for all the channels now
    if calculate_osgb:
        lon, lat = scene[band].attrs["area"].get_lonlats()
        osgb_x, osgb_y = lat_lon_to_osgb(lat, lon)
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

    for name in ["x", "y"]:
        dataarray[name].attrs["coordinate_reference_system"] = "geostationary"
    log.info("Calculated OSGB", memory=get_memory())
    # Round to the nearest 5 minutes
    dataarray.attrs.update(data_attrs)
    dataarray.attrs["end_time"] = pd.Timestamp(dataarray.attrs["end_time"]).round("5 min")

    # Rename x and y to make clear the coordinate system they are in
    dataarray = dataarray.rename({"x": "x_geostationary", "y": "y_geostationary"})
    if "time" not in dataarray.dims:
        time = pd.to_datetime(pd.Timestamp(dataarray.attrs["end_time"]).round("5 min"))
        dataarray = add_constant_coord_to_dataarray(dataarray, "time", time)

    del dataarray["crs"]
    del scene
    log.debug("Finished conversion", memory=get_memory())
    return dataarray


def do_v15_rescaling(
    dataarray: xr.DataArray, mins: np.ndarray, maxs: np.ndarray, variable_order: list
) -> xr.DataArray:
    """
    Performs old version of compression, same as v15 dataset

    Args:
        dataarray: Input DataArray
        mins: Min values per channel
        maxs: Max values per channel
        variable_order: Channel ordering

    Returns:
        Xarray DataArray
    """
    dataarray = dataarray.reindex({"variable": variable_order}).transpose(
        "time", "y_geostationary", "x_geostationary", "variable"
    )
    upper_bound = (2 ** 10) - 1
    new_max = maxs - mins

    dataarray -= mins
    dataarray /= new_max
    dataarray *= upper_bound
    dataarray = dataarray.round().clip(min=0, max=upper_bound).astype(np.int16)
    return dataarray


def get_dataset_from_scene(filename: str, hrv_scaler, use_rescaler: bool, save_dir, using_backup):
    """
    Returns the Xarray dataset from the filename
    """
    if ".nat" in filename:
        log.debug(f"Loading Native {filename}", memory=get_memory())
        hrv_scene = load_native_from_zip(filename)
    else:
        log.debug(f"Loading HRIT {filename}", memory=get_memory())
        hrv_scene = load_hrit_from_zip(filename, sections=list(range(16, 25)))
    hrv_scene.load(
        [
            "HRV",
        ],
        generate=False,
    )

    log.debug("Loaded HRV", memory=get_memory())
    hrv_dataarray: xr.DataArray = convert_scene_to_dataarray(
        hrv_scene, band="HRV", area="UK", calculate_osgb=True
    )
    log.debug("Converted HRV to dataarray", memory=get_memory())
    del hrv_scene
    attrs = serialize_attrs(hrv_dataarray.attrs)
    if use_rescaler:
        hrv_dataarray = hrv_scaler.rescale(hrv_dataarray)
    else:
        hrv_dataarray = do_v15_rescaling(
            hrv_dataarray,
            variable_order=["HRV"],
            maxs=np.array([103.90016]),
            mins=np.array([-1.2278595]),
        )
    hrv_dataarray = hrv_dataarray.transpose(
        "time", "y_geostationary", "x_geostationary", "variable"
    )
    log.info("Rescaled HRV", memory=get_memory())
    hrv_dataarray = hrv_dataarray.chunk((1, 512, 512, 1))
    hrv_dataset = hrv_dataarray.to_dataset(name="data")
    hrv_dataset.attrs.update(attrs)
    log.debug("Converted HRV to DataArray", memory=get_memory())
    now_time = pd.Timestamp(hrv_dataset["time"].values[0]).strftime("%Y%m%d%H%M")

    # Check for data quality
    if not data_quality_filter(hrv_dataset):
        del hrv_dataset
        gc.collect()
        return

    save_file = os.path.join(save_dir, f"{'15_' if using_backup else ''}hrv_{now_time}.zarr.zip")
    log.debug(f"Saving HRV netcdf in {save_file}", memory=get_memory())
    save_to_zarr_to_backend(hrv_dataset, save_file)
    del hrv_dataset
    gc.collect()
    log.debug("Saved HRV to NetCDF", memory=get_memory())

def data_quality_filter(ds: xr.Dataset, threshold_fraction: float = 0.9) -> bool:
    """
    Filter out datasets with a high fraction of zeros

    Args:
        ds: Dataset to check
        threshold_fraction: Fraction of 0's where the data quality is too low, so fail the check

    Returns:
        False, if the data contains too many zeros
        True, if not
    """
    for var in ds.data_vars:
        fraction_of_zeros = np.isclose(ds[var], 0.0).mean()
        if fraction_of_zeros > threshold_fraction:
            log.debug(f"Ignoring dataset {ds} as {var} has {fraction_of_zeros} fraction of zeros"\
                      f" (threshold {threshold_fraction})")
            return False
    return True

def get_nonhrv_dataset_from_scene(
    filename: str, scaler, use_rescaler: bool, save_dir, using_backup
):
    """
    Returns the Xarray dataset from the filename
    """
    if ".nat" in filename:
        scene = load_native_from_zip(filename)
    else:
        scene = load_hrit_from_zip(filename, sections=list(range(6, 9)))
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
        ],
        generate=False,
    )
    log.debug(f"Loaded non-hrv file: {filename}", memory=get_memory())
    dataarray: xr.DataArray = convert_scene_to_dataarray(
        scene, band="IR_016", area="UK", calculate_osgb=True
    )
    log.debug(f"Converted non-HRV file {filename} to dataarray", memory=get_memory())
    del scene
    attrs = serialize_attrs(dataarray.attrs)
    if use_rescaler:
        dataarray = scaler.rescale(dataarray)
    else:
        dataarray = do_v15_rescaling(
            dataarray,
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
    dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")
    dataarray = dataarray.chunk((1, 256, 256, 1))
    dataset = dataarray.to_dataset(name="data")
    log.debug("Converted non-HRV to dataset", memory=get_memory())
    del dataarray
    dataset.attrs.update(attrs)
    log.debug("Deleted return list", memory=get_memory())
    now_time = pd.Timestamp(dataset["time"].values[0]).strftime("%Y%m%d%H%M")

    if not data_quality_filter(dataset):
        del dataset
        gc.collect()
        return

    save_file = os.path.join(save_dir, f"{'15_' if using_backup else ''}{now_time}.zarr.zip")
    log.debug(f"Saving non-HRV netcdf in {save_file}", memory=get_memory())
    save_to_zarr_to_backend(dataset, save_file)
    del dataset
    gc.collect()
    log.debug(f"Saved non-HRV file {save_file}", memory=get_memory())


def load_hrit_from_zip(filename: str, sections: list) -> Scene:
    """Load HRIT Zip from Data Tailor to Scene for use downstream tasks"""
    if os.path.exists("temp_hrit"):
        shutil.rmtree("temp_hrit/")
    with ZipFile(filename, "r") as zipObj:
        # Extract all the contents of zip file in current directory
        zipObj.extractall(path="temp_hrit")
    the_files = []
    for f in list(glob.glob("temp_hrit/*")):
        if "PRO" in f or "EPI" in f:
            the_files.append(f)
        for segment in [f"-0000{str(i).zfill(2)}" for i in sections]:
            if segment in f:
                the_files.append(f)
    scene = Scene(filenames=the_files, reader="seviri_l1b_hrit")
    return scene


def load_native_from_zip(filename: str) -> Scene:
    """Load native file"""
    scene = Scene(filenames={"seviri_l1b_native": [filename]})
    return scene


def save_native_to_zarr(
    list_of_native_files: list,
    bands: list = [
        "HRV",
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
    save_dir: str = "./",
    use_rescaler: bool = False,
    using_backup: bool = False,
) -> None:
    """
    Saves native files to NetCDF for consumer

    Args:
        list_of_native_files: List of native files to convert into a single NetCDF file
        bands: Bands to save
        save_dir: Directory to save the netcdf files
        use_rescaler: Whether to rescale between 0 and 1 or not
        using_backup: Whether the input data is the backup 15 minutely data or not
    """

    log.debug(
        f"Converting from {'HRIT' if using_backup else 'native'} to zarr in {save_dir}",
        memory=get_memory(),
    )

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
    for f in list_of_native_files:
        log.debug(f"Processing {f}", memory=get_memory())
        if "EPCT" in f:
            log.debug(f"Processing HRIT file {f}", memory=get_memory())
            if "HRV" in f:
                log.debug(f"Processing HRV {f}", memory=get_memory())
                get_dataset_from_scene(f, hrv_scaler, use_rescaler, save_dir, using_backup)
            else:
                log.debug(f"Processing non-HRV {f}", memory=get_memory())
                get_nonhrv_dataset_from_scene(f, scaler, use_rescaler, save_dir, using_backup)
        else:
            if "HRV" in bands:
                log.debug(f"Processing HRV {f}", memory=get_memory())
                get_dataset_from_scene(f, hrv_scaler, use_rescaler, save_dir, using_backup)

            log.debug(f"Processing non-HRV {f}", memory=get_memory())
            get_nonhrv_dataset_from_scene(f, scaler, use_rescaler, save_dir, using_backup)

        log.debug(f"Finished processing files: {list_of_native_files}", memory=get_memory())


def save_dataarray_to_zarr(
    dataarray: xr.DataArray,
    zarr_path: str,
    compressor_name: str,
    zarr_mode: str = "a",
    timesteps_per_chunk: int = 1,
    y_size_per_chunk: int = 256,
    x_size_per_chunk: int = 256,
    channel_chunk_size: int = 1,
) -> None:
    """
    Save an Xarray DataArray into a Zarr file

    Args:
        dataarray: DataArray to save
        zarr_path: Filename of the Zarr dataset
        compressor_name: The name of the compression algorithm to use. Must be 'bz2' or 'blosc2'.
        zarr_mode: Mode to write to the filename, either 'w' for write, or 'a' to append
        timesteps_per_chunk: Timesteps per Zarr chunk
        y_size_per_chunk: Y pixels per Zarr chunk
        x_size_per_chunk: X pixels per Zarr chunk
        channel_chunk_size: Chunk size for the Dask arrays. Must be 1 whilst using JPEG-XL
          (at least until imagecodecs implements decompressing JPEG-XL files with multiple
          images per file.)
    """
    dataarray = dataarray.transpose("time", "y_geostationary", "x_geostationary", "variable")

    # Number of timesteps, x and y size per chunk, and channels (all 12)
    chunks = (
        timesteps_per_chunk,
        x_size_per_chunk,
        y_size_per_chunk,
        channel_chunk_size,
    )
    dataarray = dataarray.chunk(chunks)

    compression_algos = {
        "bz2": numcodecs.get_codec(dict(id="bz2", level=5)),
        "blosc2": Blosc2(cname="zstd", clevel=5)
    }
    compression_algo = compression_algos[compressor_name]

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

    assert zarr_mode in ["a", "w"], "`zarr_mode` must be one of: `a`, `w`"
    extra_kwargs = zarr_mode_to_extra_kwargs[zarr_mode]

    dataset = dataarray.to_dataset(name="data")
    dataset.to_zarr(zarr_path, mode=zarr_mode, consolidated=True, compute=True, **extra_kwargs)


def add_constant_coord_to_dataarray(
    dataarray: xr.DataArray, coord_name: str, coord_val: Any
) -> xr.DataArray:
    """
    Adds a new coordinate with a constant value to the DataArray

    Args:
        dataarray: DataArrray which will have the new coords added to it
        coord_name: Name for the new coordinate dimensions
        coord_val: Value that will be assigned to the new coordinates

    Returns:
        DataArrray with the new coords added to it
    """
    dataarray = dataarray.assign_coords({coord_name: coord_val}).expand_dims(coord_name)

    return dataarray


def check_if_timestep_exists(dt: datetime.datetime, zarr_dataset: xr.Dataset) -> bool:
    """
    Check if a timestep exists within the Xarray dataset

    Args:
        dt: Datetime of the file to check
        zarr_dataset: Zarr dataset ofthe EUMETSAT data

    Returns:
        Bool whether the timestep is in the Xarray 'time' coordinate or not
    """
    dt = pd.Timestamp(dt).round("5 min")
    if dt in zarr_dataset.coords["time"].dt.round("5 min").values:
        return True
    else:
        return False


def create_markdown_table(table_info: dict, index_name: str = "Id") -> str:
    """
    Returns a formatted string for a markdown table

    according to the dictionary passed as `table_info`.  # noqa E501

    Args:
        table_info: Mapping from index to values
        index_name: Name to use for the index column

    Returns:
        md_str: Markdown formatted table string

    Example:
        >>> table_info = {
                'Apples': {
                    'Cost': '40p',
                    'Colour': 'Red/green',
                },
                'Oranges': {
                    'Cost': '50p',
                    'Colour': 'Orange',
                },
            }
        >>> md_str = create_markdown_table(table_info, index_name='Fruit')
        >>> print(md_str)
        | Fruit   | Cost   | Colour    |
        |:--------|:-------|:----------|
        | Apples  | 40p    | Red/green |
        | Oranges | 50p    | Orange    |
    """

    df_info = pd.DataFrame(table_info).T
    df_info.index.name = index_name

    md_str = df_info.to_markdown()

    return md_str


def save_to_zarr_to_backend(dataset: xr.Dataset, filename: str):
    """Save xarray to netcdf in a Database of your choice, by default: s3

    1. Save in temp local dir
    2. upload to the Database
    :param dataset: The Xarray Dataset to be save
    :param filename: The Database filename
    """

    gc.collect()
    log.info(f"Saving file to {filename}", memory=get_memory())

    with tempfile.TemporaryDirectory() as dir:
        # save locally
        path = f"{dir}/temp.zarr.zip"
        encoding = {"data": {"dtype": "int16"}}

        # make sure variable is string
        dataset = dataset.assign_coords({"variable": dataset.coords["variable"].astype(str)})

        log.debug(f"Dataset time: {dataset.time}", memory=get_memory())

        with zarr.ZipStore(path) as store:
            dataset.to_zarr(store, compute=True, mode="w", encoding=encoding, consolidated=True)

        new_times = xr.open_dataset(f"zip::{path}", engine="zarr").time
        log.debug(f"New times for {path}: {new_times}", memory=get_memory())

        log.debug(f"Saved to temporary file {path}, now pushing to {filename}", memory=get_memory())
        # save to Database
        filesystem = fsspec.open(filename).fs
        filesystem.put(path, filename)


def filter_dataset_ids_on_current_files(datasets: list, save_dir: str) -> list:
    """
    Filter dataset ids on files in a directory

    The following occurs:
    1. get ids of files that will be downloaded
    2. get datetimes of already downloaded files
    3. only keep indexes where we need to download them

    Args:
        datasets: list of datasets with ids
        save_dir: The directory where files wil be saved

    Returns:
        The filtered list of new datasets ids to download
    """
    from satip.eumetsat import eumetsat_filename_to_datetime

    ids = [dataset["id"] for dataset in datasets]
    filesystem = fsspec.open(save_dir).fs
    finished_files_not_latest = list(filesystem.glob(f"{save_dir}/*.zarr.zip"))
    log.debug(f"Found {len(finished_files_not_latest)} already downloaded in data folder")

    latest_dir = get_latest_subdir_path(save_dir)

    filesystem_latest = fsspec.open(latest_dir).fs
    finished_files_latest = list(filesystem_latest.glob(f"{latest_dir}/*.zarr.zip"))
    log.debug(f"Found {len(finished_files_latest)} already downloaded in {LATEST_DIR_NAME} folder")

    finished_files = finished_files_not_latest + finished_files_latest
    log.debug(f"Found {len(finished_files)} already downloaded")

    datetimes = [pd.Timestamp(eumetsat_filename_to_datetime(idx)).round("5 min") for idx in ids]
    if not datetimes:  # Empty list
        log.debug("No datetimes to download")
        return []
    log.debug(f"The latest datetime that we want to downloaded is {max(datetimes)}")

    finished_datetimes = []

    # get datetimes of the finished files
    for date in finished_files:
        if "latest.zarr" in date or "latest_15.zarr" in date or "tmp" in date:
            continue
        finished_datetimes.append(
            pd.to_datetime(
                date.replace("15_", "").split(".zarr.zip")[0].split("/")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
            )
        )
    if len(finished_datetimes) > 0:
        log.debug(f"The already downloaded finished datetime are {finished_datetimes}")
    else:
        log.debug("There are no files already downloaded")

    # find which indexes to remove, if file is already there
    idx_to_remove = []
    for idx, date in enumerate(datetimes):
        if date in finished_datetimes:
            idx_to_remove.append(idx)
            log.debug(f"Will not be downloading file with {date=} as already downloaded")
        else:
            log.debug(f"Will be downloading file with {date=}")
    log.debug(
        f"Will be not be downloading {len(idx_to_remove)} files "
        f"as they have already been downloaded"
    )

    # remove index
    indices = sorted(idx_to_remove, reverse=True)
    for idx in indices:
        if idx < len(datasets):
            datasets.pop(idx)
    return datasets


def get_latest_subdir_path(save_dir: str, mkdir=False) -> str:
    """
    gets the latest dir path based on a give save_dir,

    Args:
        save_dir: Directory where data is being saved
        mkdir: if True, generate latest directory if it doesn't exist
    """

    filesystem = fsspec.open(save_dir).fs
    latest_dir = os.path.join(save_dir, LATEST_DIR_NAME)
    if not filesystem.exists(latest_dir) and mkdir:
        filesystem.mkdir(latest_dir)
    return latest_dir


def move_older_files_to_different_location(save_dir: str, history_time: pd.Timestamp):
    """
    Move older files in save_dir to a different location

    Args:
        save_dir: Directory where data is being saved
        history_time: History time to keep files

    """
    latest_dir = get_latest_subdir_path(save_dir, True)

    filesystem = fsspec.open(save_dir).fs

    # Now to move into latest
    finished_files = filesystem.glob(f"{save_dir}/*.zarr.zip")

    log.info(f"Checking {save_dir}/ for moving newer files into {latest_dir}")

    # get datetimes of the finished files

    for date in finished_files:
        log.debug(f"Looking at file {date}")
        if "latest.zarr" in date or "tmp" in date:
            continue
        if "hrv" in date:
            file_time = pd.to_datetime(
                date.replace("15_", "").split(".zarr.zip")[0].split("/")[-1].split("_")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
                utc=True,
            )
        else:
            file_time = pd.to_datetime(
                date.replace("15_", "").split(".zarr.zip")[0].split("/")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
                utc=True,
            )
        if file_time > history_time:
            log.debug("Moving file into {LATEST_DIR_NAME} folder")
            # Move HRV and non-HRV to new place
            filename = f"{latest_dir}/{date.split('/')[-1]}"
            if filesystem.exists(filename):
                log.debug(f"File already in {LATEST_DIR_NAME} folder, so not moving {filename}")
            else:
                filesystem.move(date, f"{latest_dir}/{date.split('/')[-1]}")
        elif file_time < (history_time - pd.Timedelta("2 days")):
            # Delete files over 2 days old
            log.debug("Removing file over 2 days over")
            filesystem.rm(date)

    finished_files = filesystem.glob(f"{latest_dir}/*.zarr.zip")
    log.info(f"Checking {latest_dir} for older files")
    # get datetimes of the finished files
    for date in finished_files:
        log.debug(f"Looking at file {date}")
        if "latest.zarr" in date or "latest_15.zarr" in date or "tmp" in date:
            continue
        if "hrv" in date:
            file_time = pd.to_datetime(
                date.replace("15_", "").split(".zarr.zip")[0].split("/")[-1].split("_")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
                utc=True,
            )
        else:
            file_time = pd.to_datetime(
                date.replace("15_", "").split(".zarr.zip")[0].split("/")[-1],
                format="%Y%m%d%H%M",
                errors="ignore",
                utc=True,
            )
        if file_time < history_time:
            log.debug("Moving file out of {LATEST_DIR_NAME} folder")
            # Move HRV and non-HRV to new place
            filesystem.move(date, f"{save_dir}/{date.split('/')[-1]}")


def check_both_final_files_exists(save_dir: str, using_backup: bool = False):
    """Check that both final files exists"""
    latest_dir = get_latest_subdir_path(save_dir)
    hrv_filename = f"{latest_dir}/hrv_latest{'_15' if using_backup else ''}.zarr.zip"
    filename = f"{latest_dir}/latest{'_15' if using_backup else ''}.zarr.zip"

    log.debug(f"Checking {hrv_filename} and or {filename} exists")

    if fsspec.open(hrv_filename).fs.exists(hrv_filename) and fsspec.open(filename).fs.exists(
        filename
    ):
        log.debug(f"Both {hrv_filename} and {filename} exists")
        return True
    else:
        log.debug(f"Either {hrv_filename} or {filename} dont exists")
        return False

def add_backend_to_filenames(files, backend):
    """
    Add the backend prefix to file URLs based on the specified backend.

    Args:
        files (list): List of file URLs.
        backend (str): Backend type, e.g., "s3", "gs", "az", or "local".

    Returns:
        list: List of file URLs with proper backend prefixes.
    """
    if backend == "s3":
        return [f"zip:///::s3://{str(f)}" for f in files]
    elif backend == "gs":
        return [f"zip:///::gs://{str(f)}" for f in files]
    elif backend == "az":
        return [f"zip:///::az://{str(f)}" for f in files]
    elif backend == "local":
        return [str(f) for f in files]
    else:
        raise ValueError(f"Unsupported backend: {backend}")

def collate_files_into_latest(save_dir: str, using_backup: bool = False, backend: str = "s3"):
    """
    Convert individual files into single latest file for HRV and non-HRV

    Args:
        save_dir: Directory where data is being saved
        using_backup: Whether the input data is made up of the 15 minutely backup data or not
        backend: Backend type, e.g., "s3", "gs", "az", or "local"
    """
    filesystem = fsspec.open(save_dir).fs
    latest_dir = get_latest_subdir_path(save_dir)
    hrv_files = list(
        filesystem.glob(f"{latest_dir}/{'15_' if using_backup else ''}hrv_2*.zarr.zip")
    )
    if not hrv_files:  # Empty set of files, don't do anything
        return
    # Add prefix to beginning of each URL
    filename = f"{latest_dir}/hrv_latest{'_15' if using_backup else ''}.zarr.zip"
    filename_temp = f"{latest_dir}/hrv_tmp_{secrets.token_hex(6)}.zarr.zip"
    log.debug(f"Collating HRV files {filename}")
    hrv_files = add_backend_to_filenames(hrv_files, backend)  # Added backend prefix for hrv files
    log.debug(hrv_files)
    dataset = (
        xr.open_mfdataset(
            hrv_files,
            concat_dim="time",
            combine="nested",
            engine="zarr",
            consolidated=True,
            chunks="auto",
            mode="r",
        )
        .sortby("time")
        .drop_duplicates("time")
    )
    log.debug(dataset.time.values)
    save_to_zarr_to_backend(dataset, filename_temp)
    new_times = xr.open_dataset(f"zip::{filename_temp}", engine="zarr").time
    log.debug(f"{filename_temp}  {new_times}")

    # rename
    log.debug("Renaming")
    filesystem = fsspec.open(filename_temp).fs
    try:
        filesystem.rm(filename)
    except Exception as e:
        log.warn(f"Error removing {filename}: {e}", exc_info=True)
    filesystem.mv(filename_temp, filename)
    new_times = xr.open_dataset(f"zip::{filename}", engine="zarr").time
    log.debug(f"{filename} {new_times}")

    filename = f"{latest_dir}/latest{'_15' if using_backup else ''}.zarr.zip"
    filename_temp = f"{latest_dir}/tmp_{secrets.token_hex(6)}.zarr.zip"
    log.debug(f"Collating non-HRV files {filename}")
    nonhrv_files = list(
        filesystem.glob(f"{latest_dir}/{'15_' if using_backup else ''}2*.zarr.zip")
    )
    nonhrv_files = add_backend_to_filenames(nonhrv_files, backend)  # backend prefix for nonhrv
    log.debug(nonhrv_files)
    o_dataset = (
        xr.open_mfdataset(
            nonhrv_files,
            concat_dim="time",
            combine="nested",
            engine="zarr",
            consolidated=True,
            chunks="auto",
            mode="r",
        )
        .sortby("time")
        .drop_duplicates("time")
    )
    log.debug(o_dataset.time.values)
    save_to_zarr_to_backend(o_dataset, filename_temp)
    new_times = xr.open_dataset(f"zip::{filename_temp}", engine="zarr").time
    log.debug(f"{filename_temp} {new_times}")

    log.debug("Renaming")
    filesystem = fsspec.open(filename_temp).fs
    try:
        filesystem.rm(filename)
    except Exception as e:
        log.warn(f"Error removing {filename}: {e}", exc_info=True)
    filesystem.mv(filename_temp, filename)

    new_times = xr.open_dataset(f"zip::{filename}", engine="zarr", cache=False).time
    log.debug(f"{filename} {new_times}")


def get_memory() -> str:
    """
    Gets memory of process as a string
    """
    return f"{psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2} MB"
