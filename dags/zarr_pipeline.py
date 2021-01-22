"""
The airflow DAG scaffold for satip.mario.download_latest_data_pipeline

Note that this docstring must contain the strings "airflow" and "DAG" for
Airflow to properly detect it as a DAG
See: http://bit.ly/307VMum
"""
import datetime

import yaml
from dagster_airflow.factory import make_airflow_dag

################################################################################
# #
# # This environment is auto-generated from your configs and/or presets
# #
################################################################################
ENVIRONMENT = """
solids:
  download_eumetsat_files:
    inputs:
      env_vars_fp: "/srv/airflow/.env"
      data_dir: "/srv/airflow/data/raw"
      metadata_db_fp: "/srv/airflow/data/EUMETSAT_metadata.db"
      debug_fp: "/srv/airflow/logs/EUMETSAT_download.txt"
      table_id: "eumetsat.metadata"
      project_id: "solar-pv-nowcasting"
      start_date: ""
      end_date: ""
  df_metadata_to_dt_to_fp_map:
    inputs:
      data_dir: "/srv/airflow/data/raw"
  reproject_datasets:
    inputs:
      new_coords_fp: "/srv/airflow/data/intermediate/reproj_coords_TM_4km.csv"
      new_grid_fp: "/srv/airflow/data/intermediate/new_grid_4km_TM.json"
  compress_and_save_datasets:
    inputs:
      zarr_bucket: "solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/full_extent_TM_int16"
      var_name: "stacked_eumetsat_data"
  save_metadata:
    inputs:
      table_id: "eumetsat.metadata"
      project_id: "solar-pv-nowcasting"
  compress_export_then_delete_raw:
    inputs:
      data_dir: "/srv/airflow/data/raw"
      compressed_dir: "/srv/airflow/data/compressed"
      BUCKET_NAME: "solar-pv-nowcasting-data"
      PREFIX: "satellite/EUMETSAT/SEVIRI_RSS/native/"
storage:
  filesystem:
    config:
      base_dir: /srv/airflow/data

"""

################################################################################
# #
# # NOTE: these arguments should be edited for your environment
# #
################################################################################
DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.datetime(2020, 12, 14),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
}

dag, tasks = make_airflow_dag(
    module_name="satip.mario",
    pipeline_name="download_latest_data_pipeline",
    run_config=yaml.safe_load(ENVIRONMENT),
    dag_kwargs={"default_args": DEFAULT_ARGS, "max_active_runs": 1, "schedule_interval": "*/30 * * * *", "catchup": "False"},
)
