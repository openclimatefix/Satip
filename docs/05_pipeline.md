# End-to-End Pipeline




<br>

### Imports

```
#exports
import pandas as pd
import xarray as xr

from satip import eumetsat, reproj, io, gcp_helpers
from dagster import execute_pipeline, pipeline, solid, Field

import os
import glob
import dotenv
import warnings
import shutil
```

    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  4.32rows/s]
    

<br>

### Log Cleaning

We'll suppress some errors/warnings to make the logs easier to parse

```
#exports
warnings.filterwarnings('ignore', message='divide by zero encountered in true_divide')
warnings.filterwarnings('ignore', message='invalid value encountered in sin')
warnings.filterwarnings('ignore', message='invalid value encountered in cos')
warnings.filterwarnings('ignore', message='invalid value encountered in subtract')
warnings.filterwarnings('ignore', message='You will likely lose important projection information when converting to a PROJ string from another format. See: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems')
```

<br>

### Dagster Pipeline

We're now going to combine these steps into a pipeline using `dagster`, first we'll create the individual components.

```
#exports
@solid()
def download_eumetsat_files(context, env_vars_fp: str, data_dir: str, metadata_db_fp: str, debug_fp: str, table_id: str, project_id: str, start_date: str='', end_date: str='', max_mins: int=60):
    _ = dotenv.load_dotenv(env_vars_fp)
    
    if start_date == '':
        sql_query = f'select * from {table_id} where result_time = (select max(result_time) from {table_id})'
        
        latest_saved_date = gcp_helpers.query(sql_query, project_id)['result_time'].iloc[0].tz_localize(None)
        earliest_start_date = pd.Timestamp.now() - pd.Timedelta(max_mins, unit='minutes')
        
        start_date = max(earliest_start_date, latest_saved_date).strftime('%Y-%m-%d %H:%M')
        
    if end_date == '':
        end_date = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
        
    context.log.info(f'Querying data between {start_date} - {end_date}')

    dm = eumetsat.DownloadManager(os.environ.get('USER_KEY'), os.environ.get('USER_SECRET'), data_dir, metadata_db_fp, debug_fp, slack_webhook_url=os.environ.get('SLACK_WEBHOOK_URL'), slack_id=os.environ.get('SLACK_ID'))
    df_new_metadata = dm.download_date_range(start_date, end_date)

    if df_new_metadata is None:
        df_new_metadata = pd.DataFrame(columns=['result_time', 'file_name'])
    else:
        df_new_metadata = df_new_metadata.iloc[1:] # the first entry is the last one we downloaded
        
    return df_new_metadata

@solid()
def df_metadata_to_dt_to_fp_map(_, df_new_metadata, data_dir: str) -> dict:
    """
    Here we'll then identify downloaded files in 
    the metadata dataframe and return a mapping
    between datetimes and filenames
    """
    
    datetime_to_filename = (df_new_metadata
                            .set_index('result_time')
                            ['file_name']
                            .drop_duplicates()
                            .to_dict()
                           )

    datetime_to_filepath = {
        datetime: f"{data_dir}/{filename}.nat" 
        for datetime, filename 
        in datetime_to_filename.items()
        if filename != {}
    }
    
    return datetime_to_filepath

@solid()
def reproject_datasets(_, datetime_to_filepath: dict, new_coords_fp: str, new_grid_fp: str):
    reprojector = reproj.Reprojector(new_coords_fp, new_grid_fp)

    reprojected_dss = [
        (reprojector
         .reproject(filepath, reproj_library='pyresample')
         .pipe(io.add_constant_coord_to_da, 'time', pd.to_datetime(datetime))
        )
        for datetime, filepath 
        in datetime_to_filepath.items()
    ]

    if len(reprojected_dss) > 0:
        ds_combined_reproj = xr.concat(reprojected_dss, 'time', coords='all', data_vars='all')
        return ds_combined_reproj
    else:
        return xr.Dataset()

@solid()
def compress_and_save_datasets(_, ds_combined_reproj, zarr_bucket: str, var_name: str='stacked_eumetsat_data'):
    # Handle case where no new data exists
    if len(ds_combined_reproj.dims) == 0:
        print("compress_and_save_datasets: No new data to save to zarr")
        return
    
    # Compressing the datasets
    compressor = io.Compressor()

    var_name = var_name
    da_compressed = compressor.compress(ds_combined_reproj[var_name])

    # Saving to Zarr
    ds_compressed = io.save_da_to_zarr(da_compressed, zarr_bucket)
    
    return ds_compressed

@solid()
def save_metadata(context, ds_combined_compressed, df_new_metadata, table_id: str, project_id: str):
    if ds_combined_compressed is not None:
        if df_new_metadata.shape[0] > 0:
            gcp_helpers.write_metadata_to_gcp(df_new_metadata, table_id, project_id, append=True)
            context.log.info(f'{df_new_metadata.shape[0]} new metadata entries were added')
        else:
            context.log.info('No metadata was available to be added')
            
    return True

@solid()
def compress_export_then_delete_raw(context, ds_combined_compressed, data_dir: str, compressed_dir: str, BUCKET_NAME: str='solar-pv-nowcasting-data', PREFIX: str='satellite/EUMETSAT/SEVIRI_RSS/native/', ready_to_delete: bool=True):
    if ready_to_delete == True:
        eumetsat.compress_downloaded_files(data_dir=data_dir, compressed_dir=compressed_dir, log=context.log)
        eumetsat.upload_compressed_files(compressed_dir, BUCKET_NAME=BUCKET_NAME, PREFIX=PREFIX, log=None)
        
        for dir_ in [data_dir, compressed_dir]:
            context.log.info(f'Removing directory {dir_}')
            shutil.rmtree(dir_)
            os.mkdir(dir_) # recreate empty folder
```

<br>

Then we'll combine them in a pipeline

```
#exports
@pipeline
def download_latest_data_pipeline(): 
    df_new_metadata = download_eumetsat_files()
    datetime_to_filepath = df_metadata_to_dt_to_fp_map(df_new_metadata)
    ds_combined_reproj = reproject_datasets(datetime_to_filepath)
    ds_combined_compressed = compress_and_save_datasets(ds_combined_reproj)
    
    ready_to_delete = save_metadata(ds_combined_compressed, df_new_metadata)
    compress_export_then_delete_raw(ready_to_delete)
```

<br>

Which we'll now run a test with

```
run_config = {
    'solids': {
        'download_eumetsat_files': {
            'inputs': {
                'env_vars_fp': "../.env",
                'data_dir': "../data/raw",
                'metadata_db_fp': "../data/EUMETSAT_metadata.db",
                'debug_fp': "../logs/EUMETSAT_download.txt",
                'table_id': "eumetsat.metadata",
                'project_id': "solar-pv-nowcasting",
                'start_date': "",
                'end_date': ""
            },
        },
        'df_metadata_to_dt_to_fp_map': {
            'inputs': {
                'data_dir': "../data/raw"
            }
        },
        'reproject_datasets': {
            'inputs': {
                'new_coords_fp': "../data/intermediate/reproj_coords_TM_4km.csv",
                'new_grid_fp': "../data/intermediate/new_grid_4km_TM.json"
            }
        },
        'compress_and_save_datasets': {
            'inputs': {
                'zarr_bucket': "solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/full_extent_TM_int16",
                'var_name': "stacked_eumetsat_data"
            }
        },
        'save_metadata': {
            'inputs': {
                'table_id': "eumetsat.metadata",
                'project_id': "solar-pv-nowcasting"
            },
        },
        'compress_export_then_delete_raw': {
            'inputs': {
                'data_dir': "../data/raw",
                'compressed_dir': "../data/compressed",
                'BUCKET_NAME': "solar-pv-nowcasting-data",
                'PREFIX': "satellite/EUMETSAT/SEVIRI_RSS/native/",
                'ready_to_delete': True
            },
        }
    }
}

execute_pipeline(download_latest_data_pipeline, run_config=run_config)
```

    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - ENGINE_EVENT - Starting initialization of resources [asset_store].
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - ENGINE_EVENT - Finished initialization of resources [asset_store].
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - PIPELINE_START - Started execution of pipeline "download_latest_data_pipeline".
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - ENGINE_EVENT - Executing steps in process (pid: 28895)
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_START - Started execution of step "download_eumetsat_files.compute".
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "env_vars_fp" of type "String". (Type check passed).
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "data_dir" of type "String". (Type check passed).
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "metadata_db_fp" of type "String". (Type check passed).
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "debug_fp" of type "String". (Type check passed).
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "table_id" of type "String". (Type check passed).
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "project_id" of type "String". (Type check passed).
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "start_date" of type "String". (Type check passed).
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "end_date" of type "String". (Type check passed).
    2021-02-25 18:11:09 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_INPUT - Got input "max_mins" of type "Int". (Type check passed).
    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  4.29rows/s]
    2021-02-25 18:11:11 - dagster - INFO - system - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - download_eumetsat_files.compute - Querying data between 2021-02-25 17:11 - 2021-02-25 18:11
    2021-02-25 18:11:11,425 - INFO - ********** Download Manager Initialised **************
    2021-02-25 18:11:11,888 - INFO - 0 files queried, 0 found in ../data/raw, 0 to download.
    2021-02-25 18:11:11,890 - INFO - No files will be downloaded. Set DownloadManager bucket_name argument for local download
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - download_eumetsat_files.compute - STEP_SUCCESS - Finished execution of step "download_eumetsat_files.compute" in 2.21s.
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - df_metadata_to_dt_to_fp_map.compute - STEP_START - Started execution of step "df_metadata_to_dt_to_fp_map.compute".
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - df_metadata_to_dt_to_fp_map.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input df_new_metadata in memory object store using pickle.
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - df_metadata_to_dt_to_fp_map.compute - STEP_INPUT - Got input "df_new_metadata" of type "Any". (Type check passed).
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - df_metadata_to_dt_to_fp_map.compute - STEP_INPUT - Got input "data_dir" of type "String". (Type check passed).
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - df_metadata_to_dt_to_fp_map.compute - STEP_OUTPUT - Yielded output "result" of type "dict". (Type check passed).
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - df_metadata_to_dt_to_fp_map.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - df_metadata_to_dt_to_fp_map.compute - STEP_SUCCESS - Finished execution of step "df_metadata_to_dt_to_fp_map.compute" in 5.63ms.
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - reproject_datasets.compute - STEP_START - Started execution of step "reproject_datasets.compute".
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - reproject_datasets.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input datetime_to_filepath in memory object store using pickle.
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - reproject_datasets.compute - STEP_INPUT - Got input "datetime_to_filepath" of type "dict". (Type check passed).
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - reproject_datasets.compute - STEP_INPUT - Got input "new_coords_fp" of type "String". (Type check passed).
    2021-02-25 18:11:11 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - reproject_datasets.compute - STEP_INPUT - Got input "new_grid_fp" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - reproject_datasets.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - reproject_datasets.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - reproject_datasets.compute - STEP_SUCCESS - Finished execution of step "reproject_datasets.compute" in 962ms.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_and_save_datasets.compute - STEP_START - Started execution of step "compress_and_save_datasets.compute".
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_and_save_datasets.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input ds_combined_reproj in memory object store using pickle.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_and_save_datasets.compute - STEP_INPUT - Got input "ds_combined_reproj" of type "Any". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_and_save_datasets.compute - STEP_INPUT - Got input "zarr_bucket" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_and_save_datasets.compute - STEP_INPUT - Got input "var_name" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_and_save_datasets.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_and_save_datasets.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_and_save_datasets.compute - STEP_SUCCESS - Finished execution of step "compress_and_save_datasets.compute" in 1.3ms.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - STEP_START - Started execution of step "save_metadata.compute".
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input ds_combined_compressed in memory object store using pickle.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input df_new_metadata in memory object store using pickle.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - STEP_INPUT - Got input "ds_combined_compressed" of type "Any". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - STEP_INPUT - Got input "df_new_metadata" of type "Any". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - STEP_INPUT - Got input "table_id" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - STEP_INPUT - Got input "project_id" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - save_metadata.compute - STEP_SUCCESS - Finished execution of step "save_metadata.compute" in 1.23ms.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_START - Started execution of step "compress_export_then_delete_raw.compute".
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input ds_combined_compressed in memory object store using pickle.
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "ds_combined_compressed" of type "Any". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "data_dir" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "compressed_dir" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "BUCKET_NAME" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "PREFIX" of type "String". (Type check passed).
    2021-02-25 18:11:12 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "ready_to_delete" of type "Bool". (Type check passed).
    2021-02-25 18:11:12 - dagster - INFO - system - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - compress_export_then_delete_raw.compute - Found 0 native files.
    

    Found 0 native files.
    Moved and compressed 0 files to ../data/compressed
    File /Users/laurence/code/Satip/nbs/../data/compressed/2020/10/01/12/04/MSG3-SEVI-MSG15-0100-NA-20201001120415.953000000Z-NA.nat.bz2 uploaded to satellite/EUMETSAT/SEVIRI_RSS/native/2020/10/01/12/04/MSG3-SEVI-MSG15-0100-NA-20201001120415.953000000Z-NA.nat.bz2.
    File /Users/laurence/code/Satip/nbs/../data/compressed/2020/10/01/12/09/MSG3-SEVI-MSG15-0100-NA-20201001120915.775000000Z-NA.nat.bz2 uploaded to satellite/EUMETSAT/SEVIRI_RSS/native/2020/10/01/12/09/MSG3-SEVI-MSG15-0100-NA-20201001120915.775000000Z-NA.nat.bz2.
    File /Users/laurence/code/Satip/nbs/../data/compressed/2020/01/01/00/04/MSG3-SEVI-MSG15-0100-NA-20200101000414.102000000Z-NA.nat.bz2 uploaded to satellite/EUMETSAT/SEVIRI_RSS/native/2020/01/01/00/04/MSG3-SEVI-MSG15-0100-NA-20200101000414.102000000Z-NA.nat.bz2.
    File /Users/laurence/code/Satip/nbs/../data/compressed/2020/01/01/00/09/MSG3-SEVI-MSG15-0100-NA-20200101000915.215000000Z-NA.nat.bz2 uploaded to satellite/EUMETSAT/SEVIRI_RSS/native/2020/01/01/00/09/MSG3-SEVI-MSG15-0100-NA-20200101000915.215000000Z-NA.nat.bz2.
    

    2021-02-25 18:11:58 - dagster - INFO - system - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - compress_export_then_delete_raw.compute - File path ../data/compressed/2020 was not removed.
    2021-02-25 18:11:58 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-02-25 18:11:58 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-02-25 18:11:58 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - compress_export_then_delete_raw.compute - STEP_SUCCESS - Finished execution of step "compress_export_then_delete_raw.compute" in 45.46s.
    2021-02-25 18:11:58 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - ENGINE_EVENT - Finished steps in process (pid: 28895) in 48.68s
    2021-02-25 18:11:58 - dagster - DEBUG - download_latest_data_pipeline - 15272dda-37f5-4b7a-b66c-71ab58f63bd8 - 28895 - PIPELINE_SUCCESS - Finished execution of pipeline "download_latest_data_pipeline".
    

    File /Users/laurence/code/Satip/nbs/../data/compressed/2020/01/01/00/14/MSG3-SEVI-MSG15-0100-NA-20200101001416.328000000Z-NA.nat.bz2 uploaded to satellite/EUMETSAT/SEVIRI_RSS/native/2020/01/01/00/14/MSG3-SEVI-MSG15-0100-NA-20200101001416.328000000Z-NA.nat.bz2.
    




    <dagster.core.execution.results.PipelineExecutionResult at 0x7fc94e591df0>


