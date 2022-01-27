"""Conversion of lat-long-coordinates to OSGB-coordinates.

Module sets up a transformer used in a transformation from lat-long
coordinates to OSGB-coordinates. For details, see comment below or
https://epsg.io/27700.

  Typical usage example:

  from satip.geospatial import lat_lon_to_osb
  lat_lon_to_osb(numeric_list_of_latitudes, numeric_list_of_longitudes)
"""

from numbers import Number
from typing import List, Tuple

import numpy as np
import pyproj

# OSGB is also called "OSGB 1936 / British National Grid -- United
# Kingdom Ordnance Survey".  OSGB is used in many UK electricity
# system maps, and is used by the UK Met Office UKV model.  OSGB is a
# Transverse Mercator projection, using 'easting' and 'northing'
# coordinates which are in meters.  See https://epsg.io/27700
OSGB = 27700

# WGS84 is short for "World Geodetic System 1984", used in GPS. Uses
# latitude and longitude.
WGS84 = 4326
WGS84_CRS = f"EPSG:{WGS84}"

# Geographic bounds for various regions of interest, in order of min_lon, min_lat, max_lon, max_lat
# (see https://satpy.readthedocs.io/en/stable/_modules/satpy/scene.html)
GEOGRAPHIC_BOUNDS = {"UK": (-16, 45, 10, 62), "RSS": (-64, 16, 83, 69)}


class Transformers:
    """
    Class to store transformation from one Grid to another.

    It's good to make this only once, but need the
    option of updating them, due to out of data grids.
    """

    def __init__(self):
        """Init"""
        self.lat_lon_to_osgb = pyproj.Transformer.from_crs(crs_from=WGS84, crs_to=OSGB)


# make the transformers
_transformers = Transformers()


def lat_lon_to_osgb(lat: List[Number], lon: List[Number]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Change lat, lon to a OSGB coordinates

    Args:
        lat: latitude
        lon: longitude

    Return: 2-tuple of x (east-west), y (north-south).

    """
    return _transformers.lat_lon_to_osgb.transform(lat, lon)
