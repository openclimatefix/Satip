"""

This script is designed to open, process, and save to a single large Zarr satellite imagery, similar to the NWP one.

Taken from tests detailed in https://github.com/openclimatefix/ocf_datapipes/issues/132, one of the fastest methods
of reading files seems to be with 12 timestep chunks, so that's how it'll be saved.

Steps:
For each year:
1. Get all file names in order
2. Give multiprocessing workers sets of 12 filenames to open at a time
3. Load sets of 12 at a time (1 chunk)
4. Give the loaded data to the main thread
5. Write chunk to disk

"""

import xarray as xr
from glob import glob
from numcodecs.registry import register_codec
from numcodecs.abc import Codec
from numcodecs.compat import ensure_contiguous_ndarray
import blosc2
import numpy as np
import os

class Blosc2(Codec):
    """Codec providing compression using the Blosc meta-compressor.
    Parameters
    ----------
    cname : string, optional
        A string naming one of the compression algorithms available within blosc, e.g.,
        'zstd', 'blosclz', 'lz4', 'lz4hc', 'zlib' or 'snappy'.
    clevel : integer, optional
        An integer between 0 and 9 specifying the compression level.
    See Also
    --------
    numcodecs.zstd.Zstd, numcodecs.lz4.LZ4
    """

    codec_id = 'blosc2'
    max_buffer_size = 2**31 - 1

    def __init__(self, cname='blosc2', clevel=5):
        self.cname = cname
        if cname == "zstd":
            self._codec = blosc2.Codec.ZSTD
        elif cname == "blosc2":
            self._codec = blosc2.Codec.BLOSCLZ
        self.clevel = clevel

    def encode(self, buf):
        buf = ensure_contiguous_ndarray(buf, self.max_buffer_size)
        return blosc2.compress(buf, codec=self._codec, clevel=self.clevel)

    def decode(self, buf, out=None):
        buf = ensure_contiguous_ndarray(buf, self.max_buffer_size)
        return blosc2.decompress(buf, out)

    def __repr__(self):
        r = '%s(cname=%r, clevel=%r)' % \
            (type(self).__name__,
             self.cname,
             self.clevel,)
        return r


register_codec(Blosc2)


def read_zarrs(files, dim, transform_func=None):
    def process_one_path(path):
        # use a context manager, to ensure the file gets closed after use
        with xr.open_dataset(path) as ds:
            # transform_func should do some sort of selection or
            # aggregation
            if transform_func is not None:
                ds = transform_func(ds)
            # load all data from the transformed dataset, to ensure we can
            # use it after closing each original file
            ds.load()
            return ds

    paths = sorted(glob(files))
    datasets = [process_one_path(p) for p in paths]
    combined = xr.concat(datasets, dim)
    return combined


def preprocess_function(xr_data: xr.Dataset) -> xr.Dataset:
    attrs = xr_data.attrs
    y_coords = xr_data.coords["y_geostationary"].values
    x_coords  = xr_data.coords["x_geostationary"].values
    x_dataarray = xr.DataArray(data=np.expand_dims(xr_data.coords["x_geostationary"].values, axis=0),
                               dims=["time", "x_geostationary"],
                               coords=dict(time=xr_data.coords["time"].values, x_geostationary=x_coords))
    y_dataarray = xr.DataArray(data=np.expand_dims(xr_data.coords["y_geostationary"].values, axis=0),
                               dims=["time", "y_geostationary"],
                               coords=dict(time=xr_data.coords["time"].values, y_geostationary=y_coords))
    xr_data["x_geostationary_coordinates"] = x_dataarray
    xr_data["y_geostationary_coordinates"] = y_dataarray
    xr_data.attrs = attrs
    return xr_data


def read_hrv_timesteps_and_return(files):
    dataset = xr.open_mfdataset(
        files,
        chunks="auto",  # See issue #456 for why we use "auto".
        mode="r",
        engine="zarr",
        concat_dim="time",
        consolidated=True,
        combine="nested",
    ).load().chunk({"time": 12,  "x_geostationary": int(5568/4), "y_geostationary": int(4176/4), "variable": -1})

    return dataset


def read_nonhrv_timesteps_and_return(files):
    dataset = xr.open_mfdataset(
        files,
        chunks="auto",  # See issue #456 for why we use "auto".
        mode="r",
        engine="zarr",
        concat_dim="time",
        consolidated=True,
        combine="nested",
    ).load().chunk({"time": 12,  "x_geostationary": int(3712/4), "y_geostationary": 1392, "variable": -1})

    return dataset


def write_to_zarr(dataset, zarr_name, mode):
    mode_extra_kwargs = {
        "a": {"append_dim": "time"},
        "w": {
            "encoding": {
                "time": {"units": "nanoseconds since 1970-01-01"},
            }
        },
    }
    extra_kwargs = mode_extra_kwargs[mode]
    dataset.to_zarr(zarr_name, compute=True, **extra_kwargs, consolidated=True, mode=mode)


import warnings
import dask

dask.config.set(**{"array.slicing.split_large_chunks": False})
warnings.filterwarnings("ignore", category=RuntimeWarning)
years = list(range(2022, 2013, -1))

for year in years:
    pattern = f"{year}"
    # Get all files for a month, and use that as the name for the empty one, zip up at end and download
    data_files = sorted(list(glob.glob(os.path.join(
        "/mnt/leonardo/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v6/",
        f"{pattern}*.zarr.zip"))))
    print(len(data_files))
    hrv_data_files = sorted(list(glob.glob(os.path.join(
        "/mnt/leonardo/storage_a/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v6/",
        f"hrv_{pattern}*.zarr.zip"))))
    print(len(hrv_data_files))

