"""Serialises attributes.

Function to ensure that each value of a dictionary can be serialised,
because we need a JSON-format and JSON is picky.

Usage example:
  from satip.serialize import serialize_attrs
  serialize_attrs(attribute_dictionary)
"""

import datetime

import numpy as np
import pyresample
import yaml


def serialize_attrs(attrs: dict) -> dict:
    """Ensure each value of dict can be serialized.

    This is required before saving to Zarr because Zarr represents attrs values in a
    JSON file (.zmetadata).

    The `area` field (which is a `pyresample.geometry.AreaDefinition` object gets turned
    into a YAML string, which can be loaded again using
    `area_definition = pyresample.area_config.load_area_from_string(data_array.attrs['area'])`

    Returns attrs dict where every value has been made serializable.
    """
    for key, value in attrs.items():
        # Convert Dicts
        if isinstance(value, dict):
            # Convert np.float32 to Python floats (otherwise yaml.dump complains)
            for inner_key in value:
                inner_value = value[inner_key]
                if isinstance(inner_value, np.floating):
                    value[inner_key] = float(inner_value)
            attrs[key] = yaml.dump(value)

        # Convert Numpy bools
        if isinstance(value, (bool, np.bool_)):
            attrs[key] = str(value)

        # Convert area
        if isinstance(value, pyresample.geometry.AreaDefinition):
            attrs[key] = value.dump()

        if isinstance(value, datetime.datetime):
            attrs[key] = value.isoformat()

    return attrs
