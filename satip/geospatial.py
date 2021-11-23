import datetime
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

# Geographic bounds for various regions of interest, in order of min_lon, max_lon, min_lat, max_lat
GEOGRAPHIC_BOUNDS = {"UK": (-16, 45, 10, 62)}


class Transformers:
    """
    Class to store transformation from one Grid to another.

    Its good to make this only once, but need the
    option of updating them, due to out of data grids.
    """

    def __init__(self):
        """Init"""
        self._lat_lon_to_osgb = None
        self.make_transformers()

    def make_transformers(self):
        """
        Make transformers

         Nice to only make these once, as it makes calling the functions below quicker
        """
        self._lat_lon_to_osgb = pyproj.Transformer.from_crs(crs_from=WGS84, crs_to=OSGB)

    @property
    def lat_lon_to_osgb(self):
        """lat-lon to OSGB property"""
        return self._lat_lon_to_osgb


# make the transformers
transformers = Transformers()


def download_grids():
    """The transformer grid sometimes need updating"""
    pyproj.transformer.TransformerGroup(crs_from=WGS84, crs_to=OSGB).download_grids(verbose=True)

    transformers.make_transformers()


def lat_lon_to_osgb(lat: List[Number], lon: List[Number]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Change lat, lon to a OSGB coordinates

    Args:
        lat: latitude
        lon: longitude

    Return: 2-tuple of x (east-west), y (north-south).

    """
    return transformers.lat_lon_to_osgb.transform(lat, lon)
