# Satip

[![PyPI version](https://badge.fury.io/py/satip.svg)](https://badge.fury.io/py/satip)

[![codecov](https://codecov.io/gh/openclimatefix/Satip/branch/main/graph/badge.svg?token=GTQDR2ZZ2S)](https://codecov.io/gh/openclimatefix/Satip)

> Satip is a library for <b>sat</b>ellite <b>i</b>mage <b>p</b>rocessing, and provides all of the functionality necessary for retrieving, and storing EUMETSAT data

<br>

### Installation

To install the `satip` library please run:

```bash
pip install satip
```

Or if you're working in the development environment you can run the following from the directory root:

```bash
pip install -e .
```

#### Conda

Or, if you want to use `conda` from the a cloned Satip repository:

```bash
conda env create -f environment.yml
conda activate satip
pip install -e .
```

If you plan to work on the development of Satip then also consider installing these development tools:

```bash
conda install pytest flake8 jedi mypy black pre-commit
pre-commit install
```

## Operation

### Downloading EUMETSAT Data

The following command will download the last 2 hours of RSS imagery into NetCDF files at the specified location

```bash
python scripts/app.py --api-key=<EUMETSAT API Key> --api-secret=<EUMETSAT API Secret> --save-dr="/path/to/saving/files/" --history="2 hours"
```

To download more historical data, the command below will download the native files, compress with bz2, and save into a subdirectory.

```bash
python scripts/get_raw_eumetsat_data.py --user-key=<EUMETSAT API Key> --user-secret=<EUMETSAT API Secret>
```

### Converting Native files to Zarr
`scripts/convert_native_to_zarr.py` converts EUMETSAT `.nat` files to Zarr datasets, using very mild lossy [JPEG-XL](https://en.wikipedia.org/wiki/JPEG_XL) compression. (JPEG-XL is the "new kid on the block" of image compression algorithms). JPEG-XL makes the files about a quarter the size of the equivalent `bz2` compressed files, whilst the images are visually indistinguishable. JPEG-XL cannot represent NaNs so NaNs. JPEG-XL understands float32 values in the range `[0, 1]`. NaNs are encoded as the value `0.025`. All "real" values are in the range `[0.075, 1]`. We leave a gap between "NaNs" and "real values" because there is very slight "ringing" around areas of constant value (see [this comment for more details](https://github.com/openclimatefix/Satip/issues/67#issuecomment-1036456502)). Use `satip.jpeg_xl_float_with_nans.JpegXlFloatWithNaNs` to decode the satellite data. This class will reconstruct the NaNs and rescale the data to the range `[0, 1]`.


## Testing

To run tests, simply run ```pytest .``` from the root of the repository. To generate the test plots, run ```python scripts/generate_test_plots.py```.
