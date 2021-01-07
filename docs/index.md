# Welcome to the Satip Documentation Site

<br>

> Satip is a library for <b>sat</b>ellite <b>i</b>mage <b>p</b>rocessing, and provides all of the functionality necessary for retrieving, transforming and storing EUMETSAT data

This site provides user-guides, developer documentation and other information about the `satip` module

<br>

### Installation

To install the `satip` library please run:

```bash
pip install satip
```

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

To run the *dagster* pipeline for continuous data retrieval you can use: `dagster pipeline execute -m satip.mario -c pipeline_inputs.yaml`
