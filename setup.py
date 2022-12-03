""" Satip

https://badge.fury.io/py/satip

Satip is a library for SATellite Image Processing (=SATIP), and provides all the
functionality necessary for retrieving, and storing EUMETSAT data.

For more detailed information, please check the accompanying README.md.
"""
from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
install_requires = (this_directory / "requirements.txt").read_text().splitlines()

setup(
    name="satip",
    version="2.10.23",
    license="MIT",
    description="""Satip provides the functionality necessary for
                   retrieving, and storing EUMETSAT data""",
    author="Jacob Bieker, Ayrton Bourn, Jack Kelly",
    author_email="info@openclimatefix.org",
    company="Open Climate Fix Ltd",
    install_requires=install_requires,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
)
