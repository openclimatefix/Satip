# Satip

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Future-Energy-Associates/Satip/master?urlpath=lab) [![PyPI version](https://badge.fury.io/py/satip.svg)](https://badge.fury.io/py/satip)

> Satip is a library for <b>sat</b>ellite <b>i</b>mage <b>p</b>rocessing, and provides all of the functionality necessary for retrieving, transforming and storing EUMETSAT data

<br>

### Installation

To install the `satip` library please run:

```bash
pip install satip
```

<br>

### Goals

- [x] Entire EUMETSAT SEVIRI RSS archive available as one big Zarr array (tens of TBytes) in Google Public Datasets bucket, spatially reprojected, and saved in a very space-efficient way.
- [x] Automatic job to update archive on GCP from EUMETSAT's new API once a day (Now running every half-hour).
- [x] Documentation.  Possibly user-editable.  (source on GitHub, maybe?)
- [ ] A few example Jupyter Notebooks showing how to load the data, train simple ML model, and compute metrics.

N.b. on the last goal we currently having the data loading example, as well as other examples for how to interface with the satip library. We still need to add an ML example, which we will do with a custom data-loader from Zarr.

<br>

### Notebooks 

| Id            | Directory   | Number   | Description                                        | Maintainer      |
|:--------------|:------------|:---------|:---------------------------------------------------|:----------------|
| Utilities     | nbs         | 00       | Code for keeping the repository tidy               | Ayrton Bourn    |
| EUMETSAT      | nbs         | 01       | Development of the API wrapper for ems             | Ayrton Bourn    |
| Reprojection  | nbs         | 02       | Development of the reprojection operator           | Ayrton Bourn    |
| Zarr          | nbs         | 03       | Development of wrappers for loading/saving to Zarr | Ayrton Bourn    |
| GCP           | nbs         | 04       | Development of GCP interface wrappers              | Laurence Watson |
| Pipeline      | nbs         | 05       | Development of the pipeline processes              | Ayrton Bourn    |
| Downloading   | nbs         | 101      | Guidance for using the ems download manager        | Ayrton Bourn    |
| Reprojecting  | nbs         | 102      | Guidance for using the reprojection operator       | Ayrton Bourn    |
| Loading       | nbs         | 103      | Guidance for retrieving saved data from Zarr       | Ayrton Bourn    |
| Documentation | docs        | -        | Automated generation of docs from notebooks        | Ayrton Bourn    |

<br>

### Development Set-Up

To create a new environment you can follow the following code blocks or run the `setup_env` batch script located in the batch_scripts directory.

```
git clone
conda env create -f environment.yml
conda activate sat_image_processing
```

We'll also install Jupyter lab interactive plotting for matplotlib

See the [jupyter-matplotlib docs for more info](https://github.com/matplotlib/jupyter-matplotlib).  The short version is to run these commands from within the `sat_image_processing` env:

```
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install jupyter-matplotlib
```

<br>

### Publishing to PyPi

To publish the `satip` module to PyPi simply run the following from the batch_scripts directory

```bash
pypi_publish <anaconda_dir>
```

Where `<anaconda_dir>` is the path to your anaconda directory - e.g. C:\Users\User\anaconda3

When prompted you should enter your PyPi username and password

After this you will be able to install the latest version of satip using `pip install satip`

<br>

### Pipeline

To run the *dagster* pipeline you can use: `dagster pipeline execute -m satip.mario -c pipeline_inputs.yaml`
