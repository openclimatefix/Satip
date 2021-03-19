"""
The airflow DAG scaffold for satip.backfill.download_missing_data_pipeline

Note that this docstring must contain the strings "airflow" and "DAG" for
Airflow to properly detect it as a DAG
See: http://bit.ly/307VMum

This dag uses an Airflow variable containing the run config - 
add it using the Airflow UI.
Example run config:

{
  'solids': {
      'download_missing_eumetsat_files': {
          'inputs': {
              'env_vars_fp': "../.env",
              'data_dir': "../data/raw_bfill",
              'metadata_db_fp': "../data/EUMETSAT_metadata.db",
              'debug_fp': "../logs/EUMETSAT_download.txt",
              'table_id': "eumetsat.metadata",
              'project_id': "solar-pv-nowcasting",
              'start_date': "2019-04-01T00:00:00",
              'end_date': "2019-04-01T05:00:00"
          },
      },
      'df_metadata_to_dt_to_fp_map': {
          'inputs': {
              'data_dir': "../data/raw_bfill"
          }
      },
      'reproject_compress_save_datasets_batch': {
          'inputs': {
              'new_coords_fp': "../data/intermediate/reproj_coords_TM_4km.csv",
              'new_grid_fp': "../data/intermediate/new_grid_4km_TM.json",
              'zarr_bucket': "solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/zarr_full_extent_TM_int16",
              'var_name': "stacked_eumetsat_data"
          }
      },
      'save_metadata_batch': {
          'inputs': {
              'table_id': "eumetsat.metadata",
              'project_id': "solar-pv-nowcasting"
          },
      },
      'compress_export_then_delete_raw_batch': {
          'inputs': {
              'BUCKET_NAME': "solar-pv-nowcasting-data",
              'PREFIX': "satellite/EUMETSAT/SEVIRI_RSS/native/",
              'data_dir': "../data/raw_bfill",
              'compressed_dir': "../data/compressed_bfill",
          },
      }
  }
"""
import datetime
from airflow.models import Variable
from dagster_airflow.factory import make_airflow_dag

backfill_config = Variable.get("backfill_config", deserialize_json=True)

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.datetime(2020, 12, 14),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
}

dag, tasks = make_airflow_dag(
    module_name="satip.backfill",
    pipeline_name="download_missing_data_pipeline",
    run_config=backfill_config,
    dag_kwargs={"default_args": DEFAULT_ARGS, "max_active_runs": 1, "catchup": "False"},
)
