from satpy import Scene, MultiScene
from glob import glob
from satpy.multiscene import timeseries
from satip.compression import Compressor, is_dataset_clean
import numpy as np
from imagecodecs.numcodecs import register_codecs
import xarray as xr
import zarr
import numcodecs
from satip.utils import convert_scene_to_dataarray

register_codecs()

from numcodecs.abc import Codec
from numcodecs.compat import \
    ensure_bytes, \
    ensure_contiguous_ndarray, \
    ndarray_copy
from numcodecs.registry import register_codec
import imagecodecs
import numpy as np

import matplotlib.pyplot as plt
"""
cloudmask_original = xr.open_zarr("/run/media/jacob/data/cloudmask_zarr_2017_07.zarr/cloudmask_zarr_2017_07.zarr", consolidated = True)

one_date = cloudmask_original.isel(time=1, x_osgb=slice(0,1800), y_osgb=slice(0,1800)).plot()
print(one_date)
one_date.plot.imshow()
exit()


exit()
print(cloudmask_original)
chunks = {"time": 256,"y_osgb": 512,"x_osgb": 512,"variable": 1}
cloudmask_original = cloudmask_original.chunk(chunks).astype("int8")

zarr_mode_to_extra_kwargs = {
    "a": {"append_dim": "time"},
    "w": {
        "encoding": {
            "stacked_eumetsat_data": {
                "compressor": zarr.Blosc(cname="zstd", clevel=5),
                "chunks": (256,512,512,1),
                },
            "time": {"units": "nanoseconds since 1970-01-01"},
            }
        },
    }

extra_kwargs = zarr_mode_to_extra_kwargs["w"]
zarr_path = "/run/media/jacob/data/cloudmask_2017_07_int.zarr"
extra_kwargs["encoding"]["stacked_eumetsat_data"]["compressor"] = numcodecs.get_codec(dict(id='bz2', level=5))
cloudmask_original.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)

cloudmask_original = xr.open_zarr("/run/media/jacob/data/cloudmask_zarr_2010_08.zarr/cloudmask_zarr_2010_08.zarr", consolidated = True)
print(cloudmask_original)
chunks = {"time": 256,"y_osgb": 512,"x_osgb": 512,"variable": 1}
cloudmask_original = cloudmask_original.chunk(chunks).astype("int8")
zarr_path = "/run/media/jacob/data/cloudmask_2010_08_int.zarr"
cloudmask_original.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)

cloudmask_original = xr.open_zarr("/run/media/jacob/data/cloudmask_zarr_2017_03.zarr/cloudmask_zarr_2017_03.zarr", consolidated = True)
print(cloudmask_original)
chunks = {"time": 256,"y_osgb": 512,"x_osgb": 512,"variable": 1}
cloudmask_original = cloudmask_original.chunk(chunks).astype("int8")
zarr_path = "/run/media/jacob/data/cloudmask_2017_03_int.zarr"
cloudmask_original.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)

cloudmask_original = xr.open_zarr("/run/media/jacob/data/cloudmask_zarr_2010_02.zarr/cloudmask_zarr_2010_02.zarr", consolidated = True)
print(cloudmask_original)
chunks = {"time": 256,"y_osgb": 512,"x_osgb": 512,"variable": 1}
cloudmask_original = cloudmask_original.chunk(chunks).astype("int8")
zarr_path = "/run/media/jacob/data/cloudmask_2010_02_int.zarr"
cloudmask_original.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)
exit()
"""


class jpeg2k(Codec):
    """Codec providing jpeg2k compression via imagecodecs.
    Parameters
    ----------
    level : int
        Compression level defined by imagecodecs. Relates to peak
        signal-to-noise ratio (PSNR). May need to be the reverse of PSNR
        (eg. 40 PSNR = compression level 60 | 90 PSNR = compression level 10).
    """

    codec_id = "jpeg2k"

    def __init__(self, level=50):
        self.level = level
        assert (self.level > 0 and self.level <= 100
                and isinstance(self.level, int))
        super().__init__()

    def encode(self, buf):
        return imagecodecs.jpeg2k_encode(np.squeeze(buf), level=self.level)

    def decode(self, buf, out=None):
        buf = ensure_bytes(buf)
        decoded = imagecodecs.jpeg2k_decode(buf)
        if out is not None:
            out_view = ensure_contiguous_ndarray(out)
            ndarray_copy(decoded, out_view)
        else:
            out = decoded
        return out


register_codec(jpeg2k)

class avif(Codec):
    """Codec providing jpeg2k compression via imagecodecs.
    Parameters
    ----------
    level : int
        Compression level defined by imagecodecs. Relates to peak
        signal-to-noise ratio (PSNR). May need to be the reverse of PSNR
        (eg. 40 PSNR = compression level 60 | 90 PSNR = compression level 10).
    """

    codec_id = "avif"

    def __init__(self, level=50):
        self.level = level
        assert (self.level > 0 and self.level <= 100
                and isinstance(self.level, int))
        super().__init__()

    def encode(self, buf):
        return imagecodecs.avif_encode(np.squeeze(buf), level=self.level)

    def decode(self, buf, out=None):
        buf = ensure_bytes(buf)
        decoded = imagecodecs.avif_decode(buf)
        if out is not None:
            out_view = ensure_contiguous_ndarray(out)
            ndarray_copy(decoded, out_view)
        else:
            out = decoded
        return out


register_codec(avif)

filenames = sorted(glob("/run/media/jacob/data/*.nat"))
print(filenames)

# Load multiple timesteps
compressor = Compressor(
    variable_order=["HRV"], maxs=np.array([103.90016]), mins=np.array([-1.2278595])
    )
scenes = []
for f in filenames:
    scene = Scene(filenames={"seviri_l1b_native": [f]})
    scene.load(["HRV",])
    scene["HRV"] = scene["HRV"].drop_vars("acq_time", errors="ignore")
    dataarray = convert_scene_to_dataarray(scene, 'HRV', 'RSS')
    dataarray = compressor.compress(dataarray)
    scenes.append(dataarray)

#scene = MultiScene(scenes)
#scene.load(["HRV"])
#blended_scene = scene.blend(blend_function=timeseries)

print(scenes[0])
dataarray = scenes[0]
for scene in scenes[1:]:
    try:
        dataarray = xr.concat([dataarray, scene], dim='time')
    except Exception as e:
        print(e)
print(dataarray)


dataarray = dataarray.transpose(*["time", "x_osgb", "y_osgb", "variable"])

# Number of timesteps, x and y size per chunk, and channels (all 12)
chunks = (
    1,
    256,
    256,
    1,
    )
dataarray = dataarray.chunk(chunks)
dataarray = dataarray.fillna(-1)  # Fill NaN with 65535 for uint16, even if none should exist

print(dataarray)

dataarray = xr.Dataset({"stacked_eumetsat_data": dataarray})

dataarray = dataarray.astype("int16")

zarr_mode_to_extra_kwargs = {
    "a": {"append_dim": "time"},
    "w": {
        "encoding": {
            "stacked_eumetsat_data": {
                "compressor": zarr.Blosc(cname="zstd", clevel=5),
                "chunks": chunks,
                },
            "time": {"units": "nanoseconds since 1970-01-01"},
            }
        },
    }

extra_kwargs = zarr_mode_to_extra_kwargs["w"]

import zfpy
zarr_path = "/run/media/jacob/data/hrv.zarr"
extra_kwargs["encoding"]["stacked_eumetsat_data"]["compressor"] = numcodecs.get_codec(dict(id='bz2', level=5))
dataarray.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)
exit()
zarr_path = "/run/media/jacob/data/bz2_7_int.zarr"
extra_kwargs["encoding"]["stacked_eumetsat_data"]["compressor"] = numcodecs.get_codec(dict(id='bz2', level=7))
dataarray.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)
zarr_path = "/run/media/jacob/data/bz2_9_int.zarr"
extra_kwargs["encoding"]["stacked_eumetsat_data"]["compressor"] = numcodecs.get_codec(dict(id='bz2', level=9))
dataarray.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)
exit()
#zarr_path = "/run/timeshift/backup/default.zarr"
#dataarray.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)

# Compression 2
zarr_path = "/run/timeshift/backup/jpeg2k.zarr"
extra_kwargs["encoding"]["stacked_eumetsat_data"]["compressor"] = numcodecs.get_codec(dict(id="jpeg2k", level=100))
dataarray.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)

zarr_check = xr.open_zarr(zarr_path, consolidated = True)
print(zarr_check)
print(dataarray.equals(zarr_check))
exit()
print(numcodecs.get_codec(dict(id="imagecodecs_png", level=100)))
#zarr_path = "/run/timeshift/backup/png.zarr"
#extra_kwargs["encoding"]["stacked_eumetsat_data"]["compressor"] = numcodecs.get_codec(dict(id="imagecodecs_png", level=100))
#dataarray.to_zarr(zarr_path, mode="w", consolidated=True, compute=True, **extra_kwargs)
