# Satip

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Future-Energy-Associates/Satip/master?urlpath=lab) [![PyPI version](https://badge.fury.io/py/satip.svg)](https://badge.fury.io/py/satip)

> Satip is a library for <b>sat</b>ellite <b>i</b>mage <b>p</b>rocessing, and provides all of the functionality necessary for retrieving, transforming and storing EUMETSAT data

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

#### Other dependencies
`pbzip2` is used to compress files and should be installed.  
Windows: [http://gnuwin32.sourceforge.net/packages/bzip2.htm](http://gnuwin32.sourceforge.net/packages/bzip2.htm)  
Mac:  `brew install bzip2`  
Linux: ` sudo apt-get install -y pbzip2`    

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
| CI/CD         | nbs         | 06       | Development of CI/CD helper functions              | Ayrton Bourn    |
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

### Google Cloud Platform

You will need to be authenticated with Google Cloud Platform (GCP) to use much of the library - currently it is fairly tightly coupled to storage and BigQuery for saving metadata.  
Install the GCP SDK and run:  
`gcloud auth login`  
and to "generate credentials for client libraries"  
https://googleapis.dev/python/google-api-core/latest/auth.html  
`gcloud auth application-default login`  


### Publishing to PyPi

To automatically publish the `satip` module to PyPi you can add a GitHub tag of the form `v.X.X.X`, where the version number must be higher than the current one. This will also generate a GitHub release at the same time.

To manually publish the `satip` module to PyPi simply run the following from the batch_scripts directory

```bash
pypi_publish <anaconda_dir>
```

Where `<anaconda_dir>` is the path to your anaconda directory - e.g. C:\Users\User\anaconda3

When prompted you should enter your PyPi username and password

After this you will be able to install the latest version of satip using `pip install satip`

<br>

### Pipeline

To run the *dagster* pipeline you can use: `dagster pipeline execute -m satip.mario -c pipeline_inputs.yaml`
