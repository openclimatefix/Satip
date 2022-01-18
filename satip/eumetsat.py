import copy
import datetime
import os
import re
import urllib
import zipfile
from io import BytesIO
from typing import List, Union

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

from satip import utils
import numpy as np
from PIL import Image
import rasterio
from rasterio.plot import show
im = rasterio.open("/home/jacob/Development/Satip/satip/HRSEVIRI_RSS_20210430T090400Z_20210430T090400Z_epct_079a4e74_PCQ.tif")
show(im)
im.read()
print(im.count)
print(im.height)
print(im.width)
im = np.array(im)
print(im.shape)
exit()
API_ENDPOINT = "https://api.eumetsat.int"

# Data Store searching endpoint
service_search = API_ENDPOINT + "/data/search-products/os"

# Data Store downloading endpoint
service_download = API_ENDPOINT + "/data/download"

# Data Tailor products endpoint
service_products = API_ENDPOINT + "/epcs/products"

# Data Tailor chains endpoint
service_chains = API_ENDPOINT + "/epcs/chains"

# Data Tailor rois endpoint
service_rois = API_ENDPOINT + "/epcs/rois"

# Data Tailor customisations endpoint
service_customisations = API_ENDPOINT + "/epcs/customisations"

# Data Tailor download endpoint
service_DT_download = API_ENDPOINT + "/epcs/download"

# Data Tailor projections endpoint
service_projections = API_ENDPOINT + "/epcs/projections"

# Data Tailor formats endpoint
service_formats = API_ENDPOINT + "/epcs/formats"

# Data Tailor filters endpoint
service_filters = API_ENDPOINT + "/epcs/filters"


def build_url_string(url, parameters):
    """
    Builds a url string from a parameters dictionary

    Args:
        url (str):         the base URL
        parameters (dict): the query parameters

    Return:
        url (str):         the query ready URL
    """
    init=True
    for key, value in parameters.items():
        if init:
            url=url+'?'
            init=False
        else:
            url = url+'&'

        url = url + key +'=' +value

    return url

def request_access_token(user_key, user_secret):
    """
    Requests an access token from the EUMETSAT data API

    Parameters:
        user_key: EUMETSAT API key
        user_secret: EUMETSAT API secret

    Returns:
        access_token: API access token

    """

    token_url = "https://api.eumetsat.int/token"

    r = requests.post(
        token_url,
        auth=requests.auth.HTTPBasicAuth(user_key, user_secret),
        data={"grant_type": "client_credentials"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    access_token = r.json()["access_token"]

    return access_token

access_token = request_access_token("SWdEnLvOlVTVGli1An1nKJ3NcV0a", "gUQe0ej7H_MqQVGF4cd7wfQWcawa")

SEVIRI = "HRSEVIRI"
RSS_ID = "HRSEVIRI_RSS"
AMV_ID = "MSGAMVE"
CLAP_ID = "MSGCLAP"
CLM_ID = "MSGCLMK"
OPT_CLOUD_ID = "MSGOCAE"
MULTI_SENSOR_RAIN = "MSGMPEG"
import json

# get available chain configs

# Define our start and end dates for temporal subsetting
start_date = datetime.datetime(2021, 4, 30, 9, 0)
end_date = datetime.datetime(2021, 4, 30, 9, 5)

# Format our paramters for searching
dataset_parameters = {'format': 'json', 'pi': "EO:EUM:DAT:MSG:MSG15-RSS"}
dataset_parameters['dtstart'] = start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
dataset_parameters['dtend'] = end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

# Retrieve datasets that match our filter
url = service_search
response = requests.get(url, dataset_parameters)
found_data_sets = response.json()
total_data_sets = found_data_sets['properties']['totalResults']

download_urls = []
if found_data_sets:
    for selected_data_set in found_data_sets['features']:
        product_id = selected_data_set['properties']['identifier']
        download_url = service_download + '/collections/{}/products/{}' \
            .format(urllib.parse.quote("EO:EUM:DAT:MSG:MSG15-RSS"),urllib.parse.quote(product_id))
        download_urls.append(download_url)
else:
    print('No data sets found')

for download_url in download_urls:
    print(download_url)

response = requests.get(service_formats, headers={'Authorization': 'Bearer {}'.format(access_token)})

for collection in response.json()['data']:
    print(collection['id'].ljust(20) + '\t '+collection['name'])

response = requests.get(service_products,
                        headers={'Authorization': 'Bearer {}'.format(access_token)})

for collection in response.json()['data']:
    print(collection['id'].ljust(20) + '\t '+collection['name'])
    if 'HRSEVIRI' in collection['id'] and '_' not in collection['id']:
        productID = collection['id']

productID = RSS_ID

parameters = {"product" : productID}
url = build_url_string(service_chains, parameters)

response = requests.get(url, headers={'Authorization': 'Bearer {}'.format(access_token)})

count = 0
for chain in response.json()['data']:
    count = count + 1
    print('Config ('+str(count)+'):')
    print(json.dumps(chain))
    print('\n')


parameters = {"product" : productID}
url = build_url_string(service_filters, parameters)
response = requests.get(url, headers={'Authorization': 'Bearer {}'.format(access_token)})
found_filters = response.json()

print(str(found_filters['total']) + " filter(s) available for " + productID + " products :")

for collection in response.json()['data']:
    print(collection['id'].ljust(20) + '\t '+ collection['name'])

count = 0
for chain in response.json()['data']:
    count = count + 1
    print('Config ('+str(count)+'):')
    print(json.dumps(chain))
    print('\n')

chain_config={"product": RSS_ID,
              "format": "netcdf4",
              "projection": "geographic",
              "roi": "united_kingdom",
              "quicklook":
                  {"format": "png_rgb",
                   "filter": "hrseviri_rss_natural_color",
                   "stretch_method": "min_max",
                   "x_size": 500}
    }
print(chain_config)

roi = 'united_kingdom'
chain_config['roi'] = roi
formats = 'geotiff'
chain_config['format'] = 'geotiff'

parameters = {"product_paths" : download_urls[0],
              "chain_config" : json.dumps(chain_config),
              "access_token" : access_token}

response = requests.post(service_customisations, params=parameters,
                         headers={'Authorization': 'Bearer {}'.format(access_token)})
print(response)
jobID = response.json()['data'][0]

status = 'RUNNING'
sleep_time = 10 # seconds
import time
while status == 'RUNNING':
    print(status)
    access_token = request_access_token("SWdEnLvOlVTVGli1An1nKJ3NcV0a", "gUQe0ej7H_MqQVGF4cd7wfQWcawa")

    url = service_customisations+'/'+jobID
    response = requests.get(url, headers={'Authorization': 'Bearer {}'.format(access_token)})
    status = response.json()[jobID]['status']
    print('Status: '+status)
    if "DONE" in status:
        break
    elif "ERROR" in status or 'KILLED' in status:
        print('Job unsuccessful, exiting')
        break
    elif 'QUEUED' in status:
        status = 'RUNNING'
    elif "INACTIVE" in status:
        print('Job inactive; doubling status polling time (max 10 mins)')
        sleep_time = max(60*10, sleep_time*2)
    time.sleep(sleep_time)

if status == 'DONE':
    access_token = request_access_token("SWdEnLvOlVTVGli1An1nKJ3NcV0a", "gUQe0ej7H_MqQVGF4cd7wfQWcawa")

    url = service_customisations+'/'+jobID
    response = requests.get(url, headers={'Authorization': 'Bearer {}'.format(access_token)})
    results = response.json()[jobID]['output_products']
    for result in results:
        print(result)

url = service_DT_download+'?path='
for result in results:
    print('Downloading: ' + result)
    response = requests.get(url+os.path.basename(result), headers={'Authorization': 'Bearer {}'.format(access_token)})
    open(os.path.join(os.getcwd(),os.path.basename(result)), 'wb').write(response.content)
    # display images only if image available in the output products (ie no compression)
    if 'zip' not in result and 'aux' not in result:
        if 'png' in result or 'jpg' in result:
            img_output = result
print('Done!')

import imageio

if os.path.exists(os.path.join(os.getcwd(),img_output)):
    import matplotlib.pyplot as plt
    im = imageio.read(os.path.join(os.getcwd(),img_output))
    plt.imshow(im)
    plt.show()


exit()

format_dt_str = lambda dt: pd.to_datetime(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def query_data_products(
    start_date: str = "2020-01-01",
    end_date: str = "2020-01-02",
    start_index: int = 0,
    num_features: int = 10_000,
    product_id: str = "EO:EUM:DAT:MSG:MSG15-RSS",
) -> requests.models.Response:
    """
    Queries the EUMETSAT data API for the specified data
    product and date-range. The dates will accept any
    format that can be interpreted by `pd.to_datetime`.
    A maximum of 10,000 entries are returned by the API
    so the indexes of the returned entries can be specified.

    Parameters:
        start_date: Start of the query period
        end_date: End of the query period
        start_index: Starting index of returned entries
        num_features: Number of returned entries
        product_id: ID of the EUMETSAT product requested

    Returns:
        r: Response from the request

    """

    search_url = API_ENDPOINT + "/data/search-products/os"

    params = {
        "format": "json",
        "pi": product_id,
        "si": start_index,
        "c": num_features,
        "sort": "start,time,0",
        "dtstart": format_dt_str(start_date),
        "dtend": format_dt_str(end_date),
    }

    r = requests.get(search_url, params=params)

    assert r.ok, f"Request was unsuccesful: {r.status_code} - {r.text}"

    return r



def query_data_tailor(access_token):
    RSS_ID = "HRSEVIRI_RSS"
    AMV_ID = "MSGAMVE"
    CLAP_ID = "MSGCLAP"
    CLM_ID = "MSGCLMK"
    OPT_CLOUD_ID = "MSGOCAE"
    MULTI_SENSOR_RAIN = "MSGMPEG"
    import json

    # get available chain configs

    parameters = {"product" : RSS_ID}
    url = build_url_string(service_chains, parameters)

    response = requests.get(url, headers={'Authorization': 'Bearer {}'.format(access_token)})

    parameters = {"product" : RSS_ID}
    url = build_url_string(service_filters, parameters)
    response = requests.get(url, headers={'Authorization': 'Bearer {}'.format(access_token)})
    found_filters = response.json()

    print(str(found_filters['total']) + " filter(s) available for " + RSS_ID + " products :")

    for collection in response.json()['data']:
        print(collection['id'].ljust(20) + '\t '+ collection['name'])

    count = 0
    for chain in response.json()['data']:
        count = count + 1
        print('Config ('+str(count)+'):')
        print(json.dumps(chain))
        print('\n')
        if chain['name'] == 'Projection Plate-Carree with quick-look':
            chain_config = chain

    roi = 'united_kingdom'
    chain_config['roi'] = roi
    formats = 'geotiff'
    chain_config['format'] = 'netcdf4'





def identify_available_datasets(
    start_date: str, end_date: str, product_id="EO:EUM:DAT:MSG:MSG15-RSS", log=None
):
    """
    Identifies available datasets from the EUMETSAT data
    API for the specified data product and date-range.
    The dates will accept any format that can be
    interpreted by `pd.to_datetime`.

    Parameters:
        start_date: Start of the query period
        end_date: End of the query period
        product_id: ID of the EUMETSAT product requested

    Returns:
        r: Response from the request

    """
    r_json = query_data_products(start_date, end_date, product_id=product_id).json()

    num_total_results = r_json["properties"]["totalResults"]
    print(f"identify_available_datasets: found {num_total_results} results from API")
    if log:
        log.info(f"Found {len(num_total_results)} EUMETSAT dataset files")

    if num_total_results < 10_000:
        return r_json["features"]

    datasets = r_json["features"]

    # need to loop in batches of 10_000 until all results are found
    extra_loops_needed = num_total_results // 10_000

    new_end_date = datasets[-1]["properties"]["date"].split("/")[1]

    for i in range(extra_loops_needed):

        # ensure the last loop we only get the remaining assets
        if i + 1 < extra_loops_needed:
            num_features = 10_000
        else:
            num_features = num_total_results - len(datasets)

        batch_r_json = query_data_products(
            start_date, new_end_date, num_features=num_features, product_id=product_id
        ).json()
        new_end_date = batch_r_json["features"][-1]["properties"]["date"].split("/")[1]
        datasets = datasets + batch_r_json["features"]

    assert num_total_results == len(
        datasets
    ), f"Some features have not been appended - {len(datasets)} / {num_total_results}"

    return datasets


def dataset_id_to_link(collection_id, data_id, access_token):
    return (
        f"https://api.eumetsat.int/data/download/collections/{urllib.parse.quote(collection_id)}/products/{urllib.parse.quote(data_id)}"
        + "?access_token="
        + access_token
    )


def json_extract(json_obj: Union[dict, list], locators: list):
    extracted_obj = copy.deepcopy(json_obj)

    for locator in locators:
        extracted_obj = extracted_obj[locator]

    return extracted_obj


def check_valid_request(r: requests.models.Response):
    """
    Checks that the response from the request is valid

    Parameters:
        r: Response object from the request

    """

    class InvalidCredentials(Exception):
        pass

    if r.ok == False:
        if "Invalid Credentials" in r.text:
            raise InvalidCredentials("The access token passed in the API request is invalid")
        else:
            raise Exception(f"The API request was unsuccesful {r.text} {r.status_code}")

    return


class DownloadManager:
    """
    The DownloadManager class provides a handler for downloading data
    from the EUMETSAT API, managing: retrieval, logging and metadata

    """

    def __init__(
        self,
        user_key: str,
        user_secret: str,
        data_dir: str,
        log_fp: str,
        logger_name="EUMETSAT Download",
    ):
        """
        Initialises the download manager by:
        * Setting up the logger
        * Requesting an API access token
        * Configuring the download directory
        * Adding satip helper functions

        Parameters:
            user_key: EUMETSAT API key
            user_secret: EUMETSAT API secret
            data_dir: Path to the directory where the satellite data will be saved
            log_fp: Filepath where the logs will be stored

        Returns:
            download_manager: Instance of the DownloadManager class

        """

        # Configuring the logger
        self.logger = utils.set_up_logging(logger_name, log_fp)

        self.logger.info(f"********** Download Manager Initialised **************")

        # Requesting the API access token
        self.user_key = user_key
        self.user_secret = user_secret

        self.request_access_token()

        # Configuring the data directory
        self.data_dir = data_dir

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Adding satip helper functions
        self.identify_available_datasets = identify_available_datasets
        self.query_data_products = query_data_products

        return

    def request_access_token(self, user_key=None, user_secret=None):
        """
        Requests an access token from the EUMETSAT data API.
        If no key or secret are provided then they will default
        to the values provided in the download manager initialisation

        Parameters:
            user_key: EUMETSAT API key
            user_secret: EUMETSAT API secret

        Returns:
            access_token: API access token

        """

        if user_key is None:
            user_key = self.user_key
        if user_secret is None:
            user_secret = self.user_secret

        self.access_token = request_access_token(user_key, user_secret)

        return

    def download_single_dataset(self, data_link: str):
        """
        Downloads a single dataset from the EUMETSAT API

        Parameters:
            data_link: Url link for the relevant dataset

        """

        params = {"access_token": self.access_token}

        r = requests.get(data_link, params=params)
        check_valid_request(r)

        zipped_files = zipfile.ZipFile(BytesIO(r.content))
        zipped_files.extractall(f"{self.data_dir}")

        return

    def download_date_range(
        self, start_date: str, end_date: str, product_id="EO:EUM:DAT:MSG:MSG15-RSS"
    ):
        """
        Downloads a set of dataset from the EUMETSAT API
        in the defined date range and specified product

        Parameters:
            start_date: Start of the requested data period
            end_date: End of the requested data period
            product_id: ID of the EUMETSAT product requested

        """

        datasets = identify_available_datasets(start_date, end_date, product_id=product_id)
        self.download_datasets(datasets, product_id=product_id)

    def download_datasets(self, datasets, product_id="EO:EUM:DAT:MSG:MSG15-RSS", download_all=True):
        """
        Downloads a set of dataset from the EUMETSAT API
        in the defined date range and specified product

        Parameters:
            datasets: list of datasets returned by `identify_available_datasets`

        """

        # Identifying dataset ids to download
        dataset_ids = sorted([dataset["id"] for dataset in datasets])

        # Downloading specified datasets
        if not dataset_ids:
            self.logger.info("No files will be downloaded. None were found in API search.")
            return

        for dataset_id in dataset_ids:
            dataset_link = dataset_id_to_link(
                product_id, dataset_id, access_token=self.access_token
            )
            # Download the raw data
            try:
                self.download_single_dataset(dataset_link)
            except:
                self.logger.info("The EUMETSAT access token has been refreshed")
                self.request_access_token()
                dataset_link = dataset_id_to_link(
                    product_id, dataset_id, access_token=self.access_token
                )
                self.download_single_dataset(dataset_link)


def get_dir_size(directory="."):
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)

            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


def get_filesize_megabytes(filename):
    """Returns filesize in megabytes"""
    filesize_bytes = os.path.getsize(filename)
    return filesize_bytes / 1e6


def eumetsat_filename_to_datetime(inner_tar_name):
    """Takes a file from the EUMETSAT API and returns
    the date and time part of the filename"""

    p = re.compile("^MSG[123]-SEVI-MSG15-0100-NA-(\d*)\.")
    title_match = p.match(inner_tar_name)
    date_str = title_match.group(1)
    return datetime.datetime.strptime(date_str, "%Y%m%d%H%M%S")


def eumetsat_cloud_name_to_datetime(filename: str):
    """Takes a file from the EUMETSAT API and returns the date and time part of the file for Cloud mask files"""
    date_str = filename.split("0100-0100-")[-1].split(".")[0]
    return datetime.datetime.strptime(date_str, "%Y%m%d%H%M%S")
