"""
The airflow DAG to backup Zarr

Note that this docstring must contain the strings "airflow" and "DAG" for
Airflow to properly detect it as a DAG
See: http://bit.ly/307VMum

See here for documentation on GCS Airflow Operators:
https://airflow.apache.org/docs/apache-airflow-providers-google/stable/_modules/airflow/providers/google/cloud/example_dags/example_gcs_to_gcs.html
"""

import os

from airflow import models
from airflow.providers.google.cloud.operators.gcs import GCSSynchronizeBucketsOperator
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator
from airflow.utils.dates import days_ago

# Zarr directory
BUCKET_1_SRC = (
    "solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/OSGB36/all_zarr_int16"
)

copy_files_with_wildcard = GCSToGCSOperator(
    task_id="copy_files_with_wildcard",
    source_bucket=BUCKET_1_SRC,
    source_object="data/*.txt",
    destination_bucket=BUCKET_1_DST,
    destination_object="backup/",
)
