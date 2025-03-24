# Satip

⚠️ Note this repo will soon be deprecated in favour of [satellite-consumer](https://github.com/openclimatefix/satellite-consumer)

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-14-orange.svg?style=flat-square)](#contributors-)
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

Or, if you want to use `conda` from a cloned Satip repository:

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

### Development Environment

In order to contribute:
- it's recommended that you use a Linux-based OS. This is currently used for all CI/CD testing, production, and development.
- At the time of writing (21-Dec-23), the Python version used is 3.11 with work being done to update to Python 3.12. This is subject to updates over time.

## Operation

### Getting your own API key

In order to contribute to development or just test-run some scripts, you will need your own Eumetsat-API-key. Please follow these steps:

1. Go to https://eoportal.eumetsat.int and register an account.
2. You can log in and go to https://data.eumetsat.int/ to check available data services. From there go to your profile and choose the option "API key" or go to https://api.eumetsat.int/api-key/ directly.
3. Please make sure that you added the key and secret to your user's environment variables.

### Downloading EUMETSAT Data

We have moved this to [here](https://github.com/openclimatefix/dagster-dags/blob/main/containers/sat/download_process_sat.py)

### Converting Native files to Zarr
`scripts/convert_native_to_zarr.py` converts EUMETSAT `.nat` files to Zarr datasets, using very mild lossy [JPEG-XL](https://en.wikipedia.org/wiki/JPEG_XL) compression. (JPEG-XL is the "new kid on the block" of image compression algorithms). JPEG-XL makes the files about a quarter the size of the equivalent `bz2` compressed files, whilst the images are visually indistinguishable. JPEG-XL cannot represent NaNs so NaNs. JPEG-XL understands float32 values in the range `[0, 1]`. NaNs are encoded as the value `0.025`. All "real" values are in the range `[0.075, 1]`. We leave a gap between "NaNs" and "real values" because there is very slight "ringing" around areas of constant value (see [this comment for more details](https://github.com/openclimatefix/Satip/issues/67#issuecomment-1036456502)). Use `satip.jpeg_xl_float_with_nans.JpegXlFloatWithNaNs` to decode the satellite data. This class will reconstruct the NaNs and rescale the data to the range `[0, 1]`.


## Running in Production

The live service uses `app.py` as the entrypoint for running the live data download for OCF's forecasting service, and has a few configuration options, configurable by command line argument or environment variable.

`--api-key` or `API_KEY` is the EUMETSAT API key

`--api-secret` or `API_SECRET` is the EUMETSAT API secret

`--save-dir` or `SAVE_DIR` is the top level directory to save the output files, a `latest` subfolder will be added to that directory to contain the latest data

`--history` or `HISTORY` is the amount of history timesteps to use in the `latest.zarr` files

`--db-url` or `DB_URL` is the URL to the database to save to when a run has finished

`--use-rescaler` or `USE_RESCALER` tells whether to rescale the satellite data to between 0 and 1 or not when saving to disk. Primarily used as backwards compatibility for the current production models, all new training and production Zarrs should use the rescaled data.

`--use-iodc` or `USE_IODC` is an option to get the IODC satellite data

## Testing

To run tests, simply run ```pytest .``` from the root of the repository. To generate the test plots, run ```python scripts/generate_test_plots.py```.

### Environmental Variables
Some tests require environmental variables to be set that would be passed in by command line argument when running the code in production. These are as follows:
 - `EUMETSAT_USER_KEY`: the EUMETSAT API key
 - `EUMETSAT_USER_SECRET`: the EUMETSAT API secret

 These can be added using the `export` command in your shell environment. To add these permanently, the export statements can be added to the configuration file for the shell environment (e.g. "~/.bashrc" if using bash).

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://www.jacobbieker.com"><img src="https://avatars.githubusercontent.com/u/7170359?v=4?s=100" width="100px;" alt="Jacob Bieker"/><br /><sub><b>Jacob Bieker</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=jacobbieker" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://jack-kelly.com"><img src="https://avatars.githubusercontent.com/u/460756?v=4?s=100" width="100px;" alt="Jack Kelly"/><br /><sub><b>Jack Kelly</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=JackKelly" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/AyrtonB"><img src="https://avatars.githubusercontent.com/u/29051639?v=4?s=100" width="100px;" alt="Ayrton Bourn"/><br /><sub><b>Ayrton Bourn</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=AyrtonB" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://laurencewatson.com"><img src="https://avatars.githubusercontent.com/u/1125376?v=4?s=100" width="100px;" alt="Laurence Watson"/><br /><sub><b>Laurence Watson</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=Rabscuttler" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/notger"><img src="https://avatars.githubusercontent.com/u/1180540?v=4?s=100" width="100px;" alt="Notger Heinz"/><br /><sub><b>Notger Heinz</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=notger" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/peterdudfield"><img src="https://avatars.githubusercontent.com/u/34686298?v=4?s=100" width="100px;" alt="Peter Dudfield"/><br /><sub><b>Peter Dudfield</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=peterdudfield" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/norbline"><img src="https://avatars.githubusercontent.com/u/39647420?v=4?s=100" width="100px;" alt="Azah Norbline"/><br /><sub><b>Azah Norbline</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=norbline" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/TomPughe"><img src="https://avatars.githubusercontent.com/u/147526382?v=4?s=100" width="100px;" alt="Tom Pughe"/><br /><sub><b>Tom Pughe</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=TomPughe" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://huggingface.co/64bits"><img src="https://avatars.githubusercontent.com/u/40121574?v=4?s=100" width="100px;" alt="Zhenbang Feng"/><br /><sub><b>Zhenbang Feng</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=JasonFengGit" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/jsbaasi"><img src="https://avatars.githubusercontent.com/u/72830904?v=4?s=100" width="100px;" alt="jsbaasi"/><br /><sub><b>jsbaasi</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=jsbaasi" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/suleman1412"><img src="https://avatars.githubusercontent.com/u/37236131?v=4?s=100" width="100px;" alt="Suleman Karigar"/><br /><sub><b>Suleman Karigar</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=suleman1412" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://richasharma.co.in/"><img src="https://avatars.githubusercontent.com/u/41283476?v=4?s=100" width="100px;" alt="Richa"/><br /><sub><b>Richa</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/commits?author=14Richa" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://phinate.github.io"><img src="https://avatars.githubusercontent.com/u/49782545?v=4?s=100" width="100px;" alt="Nathan Simpson"/><br /><sub><b>Nathan Simpson</b></sub></a><br /><a href="https://github.com/openclimatefix/Satip/issues?q=author%3Aphinate" title="Bug reports">🐛</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/peach280"><img src="https://avatars.githubusercontent.com/u/187241561?v=4?s=100" width="100px;" alt="peach280"/><br /><sub><b>peach280</b></sub></a><br /><a href="#maintenance-peach280" title="Maintenance">🚧</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
