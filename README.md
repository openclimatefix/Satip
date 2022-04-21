# Satip
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-6-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

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

### Getting your own API key

In order to contribute to development or just test-run some scripts, you will need your own Eumetsat-API-key. Please follow these steps:

1. Go to https://eoportal.eumetsat.int and register an account.
2. You can log in and got to https://data.eumetsat.int/ to check available data services. From there go to your profile and choose the option "API key" or go to https://api.eumetsat.int/api-key/ directly.
3. Please make sure that you added the key and secret to your user's environment variables.

### Downloading EUMETSAT Data

The following command will download the last 2 hours of RSS imagery into NetCDF files at the specified location

```bash
python satip/app.py --api-key=<EUMETSAT API Key> --api-secret=<EUMETSAT API Secret> --save-dr="/path/to/saving/files/" --history="2 hours"
```

To download more historical data, the command below will download the native files, compress with bz2, and save into a subdirectory.

```bash
python satip/get_raw_eumetsat_data.py --user-key=<EUMETSAT API Key> --user-secret=<EUMETSAT API Secret>
```

### Converting Native files to Zarr
`scripts/convert_native_to_zarr.py` converts EUMETSAT `.nat` files to Zarr datasets, using very mild lossy [JPEG-XL](https://en.wikipedia.org/wiki/JPEG_XL) compression. (JPEG-XL is the "new kid on the block" of image compression algorithms). JPEG-XL makes the files about a quarter the size of the equivalent `bz2` compressed files, whilst the images are visually indistinguishable. JPEG-XL cannot represent NaNs so NaNs. JPEG-XL understands float32 values in the range `[0, 1]`. NaNs are encoded as the value `0.025`. All "real" values are in the range `[0.075, 1]`. We leave a gap between "NaNs" and "real values" because there is very slight "ringing" around areas of constant value (see [this comment for more details](https://github.com/openclimatefix/Satip/issues/67#issuecomment-1036456502)). Use `satip.jpeg_xl_float_with_nans.JpegXlFloatWithNaNs` to decode the satellite data. This class will reconstruct the NaNs and rescale the data to the range `[0, 1]`.


## Testing

To run tests, simply run ```pytest .``` from the root of the repository. To generate the test plots, run ```python scripts/generate_test_plots.py```.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://www.jacobbieker.com"><img src="https://avatars.githubusercontent.com/u/7170359?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Jacob Bieker</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=jacobbieker" title="Code">💻</a></td>
    <td align="center"><a href="http://jack-kelly.com"><img src="https://avatars.githubusercontent.com/u/460756?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Jack Kelly</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=JackKelly" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/AyrtonB"><img src="https://avatars.githubusercontent.com/u/29051639?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Ayrton Bourn</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=AyrtonB" title="Code">💻</a></td>
    <td align="center"><a href="http://laurencewatson.com"><img src="https://avatars.githubusercontent.com/u/1125376?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Laurence Watson</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=Rabscuttler" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/notger"><img src="https://avatars.githubusercontent.com/u/1180540?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Notger Heinz</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=notger" title="Documentation">📖</a></td>
    <td align="center"><a href="https://github.com/peterdudfield"><img src="https://avatars.githubusercontent.com/u/34686298?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Peter Dudfield</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=peterdudfield" title="Documentation">📖</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
