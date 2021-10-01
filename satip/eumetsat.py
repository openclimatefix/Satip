__all__ = [
    "request_access_token",
    "query_data_products",
    "format_dt_str",
    "identify_available_datasets",
    "dataset_id_to_link",
    "json_extract",
    "check_valid_request",
    "DownloadManager",
    "get_dir_size",
    "get_filesize_megabytes",
    "eumetsat_filename_to_datetime",
]

import pandas as pd

from typing import Union, List
import datetime
import zipfile
import copy
import os
from io import BytesIO
import re
import urllib

from requests.auth import HTTPBasicAuth
import requests

from satip import utils


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

    search_url = "https://api.eumetsat.int/data/search-products/os"

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
            self.logger.info(
                "No files will be downloaded. Set DownloadManager bucket_name argument for local download"
            )
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

    p = re.compile("^MSG[23]-SEVI-MSG15-0100-NA-(\d*)\.")
    title_match = p.match(inner_tar_name)
    date_str = title_match.group(1)
    return datetime.datetime.strptime(date_str, "%Y%m%d%H%M%S")
