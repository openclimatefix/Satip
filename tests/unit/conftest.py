"""Conftest

To run this tests local you may need to add
export PYTHONPATH=${PYTHONPATH}:/tests
"""

import json
import logging


class RawResponse:
    def __init__(self, filename):
        self.filename = filename
        self.finished = False
        self.name ="test hrit"

    def read(self, *args, **kwargs):
        if self.finished:
            return None

        with open(self.filename, "rb") as file:
            self.finished = True
            return file.read()

    def __len__(self):
        return 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MockResponse:
    def __init__(self, data, status_code):
        self.json_data = data
        self.status_code = status_code
        # self.content = data
        self.raw = RawResponse(data)

        if '.zip' in data:
            with open(data, "rb") as file:
                self.content = file.read()

    def json(self):
        return self.json_data

    @staticmethod
    def raise_for_status():
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def mocked_requests_get(*args, **kwargs):
    """Mocked requests get"""

    if args[0] == "https://api.eumetsat.int/data/search-products/0.4.0/os":
        filename = "data_products.json"
    elif args[0] == "https://api.eumetsat.int/data/browse/1.0.0/collections":
        filename = "collections.json"
    elif args[0] == "https://api.eumetsat.int/epcs/customisations":
        filename = "create_customisations.json"
    elif args[0] == "https://api.eumetsat.int/epcs/customisations/40cfaba7":
        filename = "update_properties.json"
    elif args[0] == "https://api.eumetsat.int/epcs/download":
        filename = "test.hrit"
    elif args[0][0:114] == "https://api.eumetsat.int/data/download/collections/EO%3AEUM%3ADAT%3AMSG%3ARSS-CLM/products/MSG3-SEVI-MSG15-0100-NA":
        filename = "test.zip"
    elif args[0][0:116] == "https://api.eumetsat.int/data/download/collections/EO%3AEUM%3ADAT%3AMSG%3AMSG15-RSS/products/MSG3-SEVI-MSG15-0100-NA":
        filename = "test.zip"
    elif args[0][0:118] == "https://api.eumetsat.int/data/download/collections/EO%3AEUM%3ADAT%3AMSG%3ARSS-CLM/products/MSG3-SEVI-MSGCLMK-0100-0100":
        filename = "test.zip"
    else:
        raise Exception(f"url string has not been mocked {args[0]} in get. All args are {args}")

    folder = "tests/unit/data"
    if ".json" in filename:
        with open(f"{folder}/{filename}") as json_file:
            data = json.load(json_file)
            return MockResponse(data, 200)
    else:
        return MockResponse(f"{folder}/{filename}", 200)


def mocked_requests_post(*args, **kwargs):
    """Mocked requests get"""

    class MockResponse:
        def __init__(self, data, status_code):
            self.json_data = data
            self.status_code = status_code
            self.content = data

        def json(self):
            return self.json_data

        def raise_for_status(self):
            return None

    if args[0] == "https://api.eumetsat.int/token":
        filename = "token.json"
    elif args[0] == "https://api.eumetsat.int/epcs/customisations":
        filename = "new_customisation.json"
    else:
        raise Exception(f"url string has not been mocked {args[0]} in post. All args are {args}")

    folder = "tests/unit/data"
    if ".json" in filename:
        with open(f"{folder}/{filename}") as json_file:
            data = json.load(json_file)
            return MockResponse(data, 200)


def mocked_requests_patch(*args, **kwargs):
    """Mocked requests get"""

    class MockResponse:
        def __init__(self, data, status_code):
            self.json_data = data
            self.status_code = status_code
            self.content = data

        def json(self):
            return self.json_data

        def raise_for_status(self):
            return None

    if args[0] == "https://api.eumetsat.int/epcs/customisations/delete":
        filename = "delete.json"
    else:
        raise Exception(f"url string has not been mocked {args[0]} in post. All args are {args}")

    folder = "tests/unit/data"
    if ".json" in filename:
        with open(f"{folder}/{filename}") as json_file:
            data = json.load(json_file)
            return MockResponse(data, 200)

