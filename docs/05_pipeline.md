# End-to-End Pipeline



```python
#exports
import pandas as pd
import xarray as xr

from satip import eumetsat, reproj, io, gcp_helpers
from dagster import execute_pipeline, pipeline, solid, Field

import os
import glob
import dotenv
import warnings
```

    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\google\auth\_default.py:69: UserWarning: Your application has authenticated using end user credentials from Google Cloud SDK without a quota project. You might receive a "quota exceeded" or "API not enabled" error. We recommend you rerun `gcloud auth application-default login` and make sure a quota project is added. Or you can use service accounts instead. For more information about service accounts, see https://cloud.google.com/docs/authentication/
      warnings.warn(_CLOUD_SDK_CREDENTIALS_WARNING)
    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  4.46rows/s]
    

<br>

### Log Cleaning

We'll suppress some errors/warnings to make the logs easier to parse

```python
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

```python
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
            files = glob.glob(f'{dir_}/*')
            
            for f in files:
                os.remove(f)
```

<br>

Then we'll combine them in a pipeline

```python
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

```python
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

    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - ENGINE_EVENT - Starting initialization of resources [asset_store].
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - ENGINE_EVENT - Finished initialization of resources [asset_store].
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - PIPELINE_START - Started execution of pipeline "download_latest_data_pipeline".
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - ENGINE_EVENT - Executing steps in process (pid: 1108)
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_START - Started execution of step "download_eumetsat_files.compute".
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "env_vars_fp" of type "String". (Type check passed).
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "data_dir" of type "String". (Type check passed).
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "metadata_db_fp" of type "String". (Type check passed).
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "debug_fp" of type "String". (Type check passed).
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "table_id" of type "String". (Type check passed).
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "project_id" of type "String". (Type check passed).
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "start_date" of type "String". (Type check passed).
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "end_date" of type "String". (Type check passed).
    2021-01-21 22:33:00 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_INPUT - Got input "max_mins" of type "Int". (Type check passed).
    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  5.00rows/s]
    2021-01-21 22:33:02 - dagster - INFO - system - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - download_eumetsat_files.compute - Querying data between 2021-01-21 21:33 - 2021-01-21 22:33
    2021-01-21 22:33:02,396 - INFO - ********** Download Manager Initialised **************
    2021-01-21 22:33:02,869 - INFO - 11 files queried, 0 found in ../data/raw, 11 to download.
    


<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:0; max-width:15ex; vertical-align:middle; text-align:right"></span>
<progress style="width:60ex" max="11" value="11" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">11/11</span>
<span class="Time-label">[01:08<00:06, 6.19s/it]</span></div>


    2021-01-21 22:34:10 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-01-21 22:34:10 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-01-21 22:34:10 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - download_eumetsat_files.compute - STEP_SUCCESS - Finished execution of step "download_eumetsat_files.compute" in 1m10s.
    2021-01-21 22:34:10 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - df_metadata_to_dt_to_fp_map.compute - STEP_START - Started execution of step "df_metadata_to_dt_to_fp_map.compute".
    2021-01-21 22:34:10 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - df_metadata_to_dt_to_fp_map.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input df_new_metadata in memory object store using pickle.
    2021-01-21 22:34:10 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - df_metadata_to_dt_to_fp_map.compute - STEP_INPUT - Got input "df_new_metadata" of type "Any". (Type check passed).
    2021-01-21 22:34:10 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - df_metadata_to_dt_to_fp_map.compute - STEP_INPUT - Got input "data_dir" of type "String". (Type check passed).
    2021-01-21 22:34:11 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - df_metadata_to_dt_to_fp_map.compute - STEP_OUTPUT - Yielded output "result" of type "dict". (Type check passed).
    2021-01-21 22:34:11 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - df_metadata_to_dt_to_fp_map.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-01-21 22:34:11 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - df_metadata_to_dt_to_fp_map.compute - STEP_SUCCESS - Finished execution of step "df_metadata_to_dt_to_fp_map.compute" in 15ms.
    2021-01-21 22:34:11 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - reproject_datasets.compute - STEP_START - Started execution of step "reproject_datasets.compute".
    2021-01-21 22:34:11 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - reproject_datasets.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input datetime_to_filepath in memory object store using pickle.
    2021-01-21 22:34:11 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - reproject_datasets.compute - STEP_INPUT - Got input "datetime_to_filepath" of type "dict". (Type check passed).
    2021-01-21 22:34:11 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - reproject_datasets.compute - STEP_INPUT - Got input "new_coords_fp" of type "String". (Type check passed).
    2021-01-21 22:34:11 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - reproject_datasets.compute - STEP_INPUT - Got input "new_grid_fp" of type "String". (Type check passed).
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\numpy\lib\function_base.py:1280: RuntimeWarning: invalid value encountered in subtract
      a = op(a[slice1], a[slice2])
    2021-01-21 22:34:59 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - reproject_datasets.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-01-21 22:34:59 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - reproject_datasets.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-01-21 22:34:59 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - reproject_datasets.compute - STEP_SUCCESS - Finished execution of step "reproject_datasets.compute" in 48.26s.
    2021-01-21 22:34:59 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_and_save_datasets.compute - STEP_START - Started execution of step "compress_and_save_datasets.compute".
    2021-01-21 22:34:59 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_and_save_datasets.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input ds_combined_reproj in memory object store using pickle.
    2021-01-21 22:34:59 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_and_save_datasets.compute - STEP_INPUT - Got input "ds_combined_reproj" of type "Any". (Type check passed).
    2021-01-21 22:34:59 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_and_save_datasets.compute - STEP_INPUT - Got input "zarr_bucket" of type "String". (Type check passed).
    2021-01-21 22:34:59 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_and_save_datasets.compute - STEP_INPUT - Got input "var_name" of type "String". (Type check passed).
    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\google\auth\_default.py:69: UserWarning: Your application has authenticated using end user credentials from Google Cloud SDK without a quota project. You might receive a "quota exceeded" or "API not enabled" error. We recommend you rerun `gcloud auth application-default login` and make sure a quota project is added. Or you can use service accounts instead. For more information about service accounts, see https://cloud.google.com/docs/authentication/
      warnings.warn(_CLOUD_SDK_CREDENTIALS_WARNING)
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_and_save_datasets.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_and_save_datasets.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_and_save_datasets.compute - STEP_SUCCESS - Finished execution of step "compress_and_save_datasets.compute" in 11m44s.
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - STEP_START - Started execution of step "save_metadata.compute".
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input ds_combined_compressed in memory object store using pickle.
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input df_new_metadata in memory object store using pickle.
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - STEP_INPUT - Got input "ds_combined_compressed" of type "Any". (Type check passed).
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - STEP_INPUT - Got input "df_new_metadata" of type "Any". (Type check passed).
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - STEP_INPUT - Got input "table_id" of type "String". (Type check passed).
    2021-01-21 22:46:43 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - STEP_INPUT - Got input "project_id" of type "String". (Type check passed).
    1it [00:03,  3.73s/it]
    2021-01-21 22:46:48 - dagster - INFO - system - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - save_metadata.compute - 10 new metadata entries were added
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - STEP_OUTPUT - Yielded output "result" of type "Any". (Type check passed).
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - OBJECT_STORE_OPERATION - Stored intermediate object for output result in memory object store using pickle.
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - save_metadata.compute - STEP_SUCCESS - Finished execution of step "save_metadata.compute" in 4.29s.
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - STEP_START - Started execution of step "compress_export_then_delete_raw.compute".
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - OBJECT_STORE_OPERATION - Retrieved intermediate object for input ds_combined_compressed in memory object store using pickle.
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "ds_combined_compressed" of type "Any". (Type check passed).
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "data_dir" of type "String". (Type check passed).
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "compressed_dir" of type "String". (Type check passed).
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "BUCKET_NAME" of type "String". (Type check passed).
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "PREFIX" of type "String". (Type check passed).
    2021-01-21 22:46:48 - dagster - DEBUG - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - STEP_INPUT - Got input "ready_to_delete" of type "Bool". (Type check passed).
    2021-01-21 22:46:48 - dagster - INFO - system - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - compress_export_then_delete_raw.compute - Found 20 native files.
    2021-01-21 22:46:48 - dagster - DEBUG - system - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - compress_export_then_delete_raw.compute - Compressing ../data/raw\MSG3-SEVI-MSG15-0100-NA-20210121204918.196000000Z-NA.nat
    

    10 rows written to BQ eumetsat.metadata, append=True
    Found 20 native files.
    

    2021-01-21 22:46:49 - dagster - ERROR - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - compress_export_then_delete_raw.compute - STEP_FAILURE - Execution of step "compress_export_then_delete_raw.compute" failed.
    
    FileNotFoundError: [WinError 2] The system cannot find the file specified
    
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\errors.py", line 180, in user_code_error_boundary
        yield
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py", line 475, in _user_event_sequence_for_step_compute_fn
        for event in iterate_with_context(raise_interrupts_immediately, gen):
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\utils\__init__.py", line 443, in iterate_with_context
        next_output = next(iterator)
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\compute.py", line 105, in _execute_core_compute
        for step_output in _yield_compute_results(compute_context, inputs, compute_fn):
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\compute.py", line 76, in _yield_compute_results
        for event in user_event_sequence:
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\definitions\decorators\solid.py", line 227, in compute
        result = fn(context, **kwargs)
      File "<ipython-input-4-b374cee63da6>", line 103, in compress_export_then_delete_raw
        eumetsat.compress_downloaded_files(data_dir=data_dir, compressed_dir=compressed_dir, log=context.log)
      File "c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\eumetsat.py", line 568, in compress_downloaded_files
        completed_process = subprocess.run(['pbzip2', '-5', full_native_filename])
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\subprocess.py", line 489, in run
        with Popen(*popenargs, **kwargs) as process:
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\subprocess.py", line 854, in __init__
        self._execute_child(args, executable, preexec_fn, close_fds,
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\subprocess.py", line 1307, in _execute_child
        hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
    
    2021-01-21 22:46:49 - dagster - ERROR - download_latest_data_pipeline - d3e2e4f6-c6a3-4ee2-af3a-2570ac7c607a - 1108 - PIPELINE_FAILURE - Execution of pipeline "download_latest_data_pipeline" failed. An exception was thrown during execution.
    
    FileNotFoundError: [WinError 2] The system cannot find the file specified
    
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py", line 665, in _pipeline_execution_iterator
        for event in pipeline_context.executor.execute(pipeline_context, execution_plan):
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\executor\in_process.py", line 36, in execute
        for event in inner_plan_execution_iterator(pipeline_context, execution_plan):
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_plan.py", line 77, in inner_plan_execution_iterator
        for step_event in check.generator(
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_plan.py", line 272, in _dagster_event_sequence_for_step
        raise dagster_user_error.user_exception
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\errors.py", line 180, in user_code_error_boundary
        yield
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py", line 475, in _user_event_sequence_for_step_compute_fn
        for event in iterate_with_context(raise_interrupts_immediately, gen):
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\utils\__init__.py", line 443, in iterate_with_context
        next_output = next(iterator)
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\compute.py", line 105, in _execute_core_compute
        for step_output in _yield_compute_results(compute_context, inputs, compute_fn):
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\compute.py", line 76, in _yield_compute_results
        for event in user_event_sequence:
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\definitions\decorators\solid.py", line 227, in compute
        result = fn(context, **kwargs)
      File "<ipython-input-4-b374cee63da6>", line 103, in compress_export_then_delete_raw
        eumetsat.compress_downloaded_files(data_dir=data_dir, compressed_dir=compressed_dir, log=context.log)
      File "c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\eumetsat.py", line 568, in compress_downloaded_files
        completed_process = subprocess.run(['pbzip2', '-5', full_native_filename])
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\subprocess.py", line 489, in run
        with Popen(*popenargs, **kwargs) as process:
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\subprocess.py", line 854, in __init__
        self._execute_child(args, executable, preexec_fn, close_fds,
      File "C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\subprocess.py", line 1307, in _execute_child
        hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
    
    


    ---------------------------------------------------------------------------

    DagsterExecutionStepExecutionError        Traceback (most recent call last)

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_plan.py in _dagster_event_sequence_for_step(step_context, retries)
        211 
    --> 212         for step_event in check.generator(step_events):
        213             yield step_event
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py in core_dagster_event_sequence_for_step(step_context, prior_attempt_count)
        285         # timer block above in order for time to be recorded accurately.
    --> 286         for user_event in check.generator(
        287             _step_output_error_checked_user_event_sequence(step_context, user_event_sequence)
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py in _step_output_error_checked_user_event_sequence(step_context, user_event_sequence)
         58 
    ---> 59     for user_event in user_event_sequence:
         60         if not isinstance(user_event, Output):
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py in _user_event_sequence_for_step_compute_fn(step_context, evaluated_inputs)
        475         for event in iterate_with_context(raise_interrupts_immediately, gen):
    --> 476             yield event
        477 
    

    ~\anaconda3\envs\satip_dev\lib\contextlib.py in __exit__(self, type, value, traceback)
        130             try:
    --> 131                 self.gen.throw(type, value, traceback)
        132             except StopIteration as exc:
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\errors.py in user_code_error_boundary(error_cls, msg_fn, control_flow_exceptions, **kwargs)
        189         # with the error reported further up the stack
    --> 190         raise_from(
        191             error_cls(msg_fn(), user_exception=e, original_exc_info=sys.exc_info(), **kwargs), e
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\future\utils\__init__.py in raise_from(exc, cause)
        402         execstr = "raise __python_future_raise_from_exc from __python_future_raise_from_cause"
    --> 403         exec(execstr, myglobals, mylocals)
        404 
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\errors.py in <module>
    

    DagsterExecutionStepExecutionError: Error occurred during the execution of step:
            step key: "compress_export_then_delete_raw.compute"
            solid invocation: "compress_export_then_delete_raw"
            solid definition: "compress_export_then_delete_raw"
            

    
    During handling of the above exception, another exception occurred:
    

    FileNotFoundError                         Traceback (most recent call last)

        [... skipping hidden 1 frame]
    

    <ipython-input-6-7ed226242252> in <module>
         49 
    ---> 50 execute_pipeline(download_latest_data_pipeline, run_config=run_config)
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in execute_pipeline(pipeline, run_config, mode, preset, tags, solid_selection, instance, raise_on_error)
        323     with _ephemeral_instance_if_missing(instance) as execute_instance:
    --> 324         return _logged_execute_pipeline(
        325             pipeline,
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\telemetry.py in wrap(*args, **kwargs)
         88         log_action(instance=instance, action=f.__name__ + "_started", client_time=start_time)
    ---> 89         result = f(*args, **kwargs)
         90         end_time = datetime.datetime.now()
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in _logged_execute_pipeline(pipeline, instance, run_config, mode, preset, tags, solid_selection, raise_on_error)
        374 
    --> 375     return execute_run(pipeline, pipeline_run, instance, raise_on_error=raise_on_error)
        376 
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in execute_run(pipeline, pipeline_run, instance, raise_on_error)
        176     )
    --> 177     event_list = list(_execute_run_iterable)
        178     pipeline_context = _execute_run_iterable.pipeline_context
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in __iter__(self)
        726                 if self.pipeline_context:  # False if we had a pipeline init failure
    --> 727                     for event in self.iterator(
        728                         execution_plan=self.execution_plan, pipeline_context=self.pipeline_context,
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in _pipeline_execution_iterator(pipeline_context, execution_plan)
        664     try:
    --> 665         for event in pipeline_context.executor.execute(pipeline_context, execution_plan):
        666             if event.is_step_failure:
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\executor\in_process.py in execute(self, pipeline_context, execution_plan)
         35         with time_execution_scope() as timer_result:
    ---> 36             for event in inner_plan_execution_iterator(pipeline_context, execution_plan):
         37                 yield event
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_plan.py in inner_plan_execution_iterator(pipeline_context, execution_plan)
         76                 else:
    ---> 77                     for step_event in check.generator(
         78                         _dagster_event_sequence_for_step(step_context, retries)
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_plan.py in _dagster_event_sequence_for_step(step_context, retries)
        271         if step_context.raise_on_error:
    --> 272             raise dagster_user_error.user_exception
        273 
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\errors.py in user_code_error_boundary(error_cls, msg_fn, control_flow_exceptions, **kwargs)
        179     try:
    --> 180         yield
        181     except control_flow_exceptions as cf:
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py in _user_event_sequence_for_step_compute_fn(step_context, evaluated_inputs)
        474         # Allow interrupts again during each step of the execution
    --> 475         for event in iterate_with_context(raise_interrupts_immediately, gen):
        476             yield event
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\utils\__init__.py in iterate_with_context(context_manager_class, iterator)
        442             try:
    --> 443                 next_output = next(iterator)
        444             except StopIteration:
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\compute.py in _execute_core_compute(compute_context, inputs, compute_fn)
        104     all_results = []
    --> 105     for step_output in _yield_compute_results(compute_context, inputs, compute_fn):
        106         yield step_output
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\compute.py in _yield_compute_results(compute_context, inputs, compute_fn)
         75 
    ---> 76     for event in user_event_sequence:
         77         if isinstance(event, (Output, AssetMaterialization, Materialization, ExpectationResult)):
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\definitions\decorators\solid.py in compute(context, input_defs)
        226 
    --> 227         result = fn(context, **kwargs)
        228 
    

    <ipython-input-4-b374cee63da6> in compress_export_then_delete_raw(context, ds_combined_compressed, data_dir, compressed_dir, BUCKET_NAME, PREFIX, ready_to_delete)
        102     if ready_to_delete == True:
    --> 103         eumetsat.compress_downloaded_files(data_dir=data_dir, compressed_dir=compressed_dir, log=context.log)
        104         eumetsat.upload_compressed_files(compressed_dir, BUCKET_NAME=BUCKET_NAME, PREFIX=PREFIX, log=None)
    

    c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\eumetsat.py in compress_downloaded_files(data_dir, compressed_dir, log)
        567 
    --> 568         completed_process = subprocess.run(['pbzip2', '-5', full_native_filename])
        569         try:
    

    ~\anaconda3\envs\satip_dev\lib\subprocess.py in run(input, capture_output, timeout, check, *popenargs, **kwargs)
        488 
    --> 489     with Popen(*popenargs, **kwargs) as process:
        490         try:
    

    ~\anaconda3\envs\satip_dev\lib\subprocess.py in __init__(self, args, bufsize, executable, stdin, stdout, stderr, preexec_fn, close_fds, shell, cwd, env, universal_newlines, startupinfo, creationflags, restore_signals, start_new_session, pass_fds, encoding, errors, text)
        853 
    --> 854             self._execute_child(args, executable, preexec_fn, close_fds,
        855                                 pass_fds, cwd, env,
    

    ~\anaconda3\envs\satip_dev\lib\subprocess.py in _execute_child(self, args, executable, preexec_fn, close_fds, pass_fds, cwd, env, startupinfo, creationflags, shell, p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite, unused_restore_signals, unused_start_new_session)
       1306             try:
    -> 1307                 hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
       1308                                          # no special security
    

    FileNotFoundError: [WinError 2] The system cannot find the file specified

    
    The above exception was the direct cause of the following exception:
    

    DagsterExecutionStepExecutionError        Traceback (most recent call last)

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_plan.py in _dagster_event_sequence_for_step(step_context, retries)
        211 
    --> 212         for step_event in check.generator(step_events):
        213             yield step_event
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py in core_dagster_event_sequence_for_step(step_context, prior_attempt_count)
        285         # timer block above in order for time to be recorded accurately.
    --> 286         for user_event in check.generator(
        287             _step_output_error_checked_user_event_sequence(step_context, user_event_sequence)
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py in _step_output_error_checked_user_event_sequence(step_context, user_event_sequence)
         58 
    ---> 59     for user_event in user_event_sequence:
         60         if not isinstance(user_event, Output):
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py in _user_event_sequence_for_step_compute_fn(step_context, evaluated_inputs)
        475         for event in iterate_with_context(raise_interrupts_immediately, gen):
    --> 476             yield event
        477 
    

    ~\anaconda3\envs\satip_dev\lib\contextlib.py in __exit__(self, type, value, traceback)
        130             try:
    --> 131                 self.gen.throw(type, value, traceback)
        132             except StopIteration as exc:
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\errors.py in user_code_error_boundary(error_cls, msg_fn, control_flow_exceptions, **kwargs)
        189         # with the error reported further up the stack
    --> 190         raise_from(
        191             error_cls(msg_fn(), user_exception=e, original_exc_info=sys.exc_info(), **kwargs), e
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\future\utils\__init__.py in raise_from(exc, cause)
        402         execstr = "raise __python_future_raise_from_exc from __python_future_raise_from_cause"
    --> 403         exec(execstr, myglobals, mylocals)
        404 
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\errors.py in <module>
    

    DagsterExecutionStepExecutionError: Error occurred during the execution of step:
            step key: "compress_export_then_delete_raw.compute"
            solid invocation: "compress_export_then_delete_raw"
            solid definition: "compress_export_then_delete_raw"
            

    
    During handling of the above exception, another exception occurred:
    

    FileNotFoundError                         Traceback (most recent call last)

    <ipython-input-6-7ed226242252> in <module>
         48 }
         49 
    ---> 50 execute_pipeline(download_latest_data_pipeline, run_config=run_config)
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in execute_pipeline(pipeline, run_config, mode, preset, tags, solid_selection, instance, raise_on_error)
        322 
        323     with _ephemeral_instance_if_missing(instance) as execute_instance:
    --> 324         return _logged_execute_pipeline(
        325             pipeline,
        326             instance=execute_instance,
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\telemetry.py in wrap(*args, **kwargs)
         87         start_time = datetime.datetime.now()
         88         log_action(instance=instance, action=f.__name__ + "_started", client_time=start_time)
    ---> 89         result = f(*args, **kwargs)
         90         end_time = datetime.datetime.now()
         91         log_action(
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in _logged_execute_pipeline(pipeline, instance, run_config, mode, preset, tags, solid_selection, raise_on_error)
        373     )
        374 
    --> 375     return execute_run(pipeline, pipeline_run, instance, raise_on_error=raise_on_error)
        376 
        377 
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in execute_run(pipeline, pipeline_run, instance, raise_on_error)
        175         ),
        176     )
    --> 177     event_list = list(_execute_run_iterable)
        178     pipeline_context = _execute_run_iterable.pipeline_context
        179 
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in __iter__(self)
        725             try:
        726                 if self.pipeline_context:  # False if we had a pipeline init failure
    --> 727                     for event in self.iterator(
        728                         execution_plan=self.execution_plan, pipeline_context=self.pipeline_context,
        729                     ):
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\api.py in _pipeline_execution_iterator(pipeline_context, execution_plan)
        663     generator_closed = False
        664     try:
    --> 665         for event in pipeline_context.executor.execute(pipeline_context, execution_plan):
        666             if event.is_step_failure:
        667                 failed_steps.append(event.step_key)
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\executor\in_process.py in execute(self, pipeline_context, execution_plan)
         34 
         35         with time_execution_scope() as timer_result:
    ---> 36             for event in inner_plan_execution_iterator(pipeline_context, execution_plan):
         37                 yield event
         38 
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_plan.py in inner_plan_execution_iterator(pipeline_context, execution_plan)
         75                     active_execution.mark_skipped(step.key)
         76                 else:
    ---> 77                     for step_event in check.generator(
         78                         _dagster_event_sequence_for_step(step_context, retries)
         79                     ):
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_plan.py in _dagster_event_sequence_for_step(step_context, retries)
        270 
        271         if step_context.raise_on_error:
    --> 272             raise dagster_user_error.user_exception
        273 
        274     # case (4) in top comment
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\errors.py in user_code_error_boundary(error_cls, msg_fn, control_flow_exceptions, **kwargs)
        178     )
        179     try:
    --> 180         yield
        181     except control_flow_exceptions as cf:
        182         # A control flow exception has occurred and should be propagated
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\execute_step.py in _user_event_sequence_for_step_compute_fn(step_context, evaluated_inputs)
        473 
        474         # Allow interrupts again during each step of the execution
    --> 475         for event in iterate_with_context(raise_interrupts_immediately, gen):
        476             yield event
        477 
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\utils\__init__.py in iterate_with_context(context_manager_class, iterator)
        441         with context_manager_class():
        442             try:
    --> 443                 next_output = next(iterator)
        444             except StopIteration:
        445                 return
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\compute.py in _execute_core_compute(compute_context, inputs, compute_fn)
        103 
        104     all_results = []
    --> 105     for step_output in _yield_compute_results(compute_context, inputs, compute_fn):
        106         yield step_output
        107         if isinstance(step_output, Output):
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\execution\plan\compute.py in _yield_compute_results(compute_context, inputs, compute_fn)
         74         return
         75 
    ---> 76     for event in user_event_sequence:
         77         if isinstance(event, (Output, AssetMaterialization, Materialization, ExpectationResult)):
         78             yield event
    

    ~\anaconda3\envs\satip_dev\lib\site-packages\dagster\core\definitions\decorators\solid.py in compute(context, input_defs)
        225             kwargs[input_name] = input_defs[input_name]
        226 
    --> 227         result = fn(context, **kwargs)
        228 
        229         if inspect.isgenerator(result):
    

    <ipython-input-4-b374cee63da6> in compress_export_then_delete_raw(context, ds_combined_compressed, data_dir, compressed_dir, BUCKET_NAME, PREFIX, ready_to_delete)
        101 def compress_export_then_delete_raw(context, ds_combined_compressed, data_dir: str, compressed_dir: str, BUCKET_NAME: str='solar-pv-nowcasting-data', PREFIX: str='satellite/EUMETSAT/SEVIRI_RSS/native/', ready_to_delete: bool=True):
        102     if ready_to_delete == True:
    --> 103         eumetsat.compress_downloaded_files(data_dir=data_dir, compressed_dir=compressed_dir, log=context.log)
        104         eumetsat.upload_compressed_files(compressed_dir, BUCKET_NAME=BUCKET_NAME, PREFIX=PREFIX, log=None)
        105 
    

    c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\eumetsat.py in compress_downloaded_files(data_dir, compressed_dir, log)
        566             log.debug(f'Compressing {full_native_filename}')
        567 
    --> 568         completed_process = subprocess.run(['pbzip2', '-5', full_native_filename])
        569         try:
        570             completed_process.check_returncode()
    

    ~\anaconda3\envs\satip_dev\lib\subprocess.py in run(input, capture_output, timeout, check, *popenargs, **kwargs)
        487         kwargs['stderr'] = PIPE
        488 
    --> 489     with Popen(*popenargs, **kwargs) as process:
        490         try:
        491             stdout, stderr = process.communicate(input, timeout=timeout)
    

    ~\anaconda3\envs\satip_dev\lib\subprocess.py in __init__(self, args, bufsize, executable, stdin, stdout, stderr, preexec_fn, close_fds, shell, cwd, env, universal_newlines, startupinfo, creationflags, restore_signals, start_new_session, pass_fds, encoding, errors, text)
        852                             encoding=encoding, errors=errors)
        853 
    --> 854             self._execute_child(args, executable, preexec_fn, close_fds,
        855                                 pass_fds, cwd, env,
        856                                 startupinfo, creationflags, shell,
    

    ~\anaconda3\envs\satip_dev\lib\subprocess.py in _execute_child(self, args, executable, preexec_fn, close_fds, pass_fds, cwd, env, startupinfo, creationflags, shell, p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite, unused_restore_signals, unused_start_new_session)
       1305             # Start the process
       1306             try:
    -> 1307                 hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
       1308                                          # no special security
       1309                                          None, None,
    

    FileNotFoundError: [WinError 2] The system cannot find the file specified


```python
#exports
@solid()
def download_missing_eumetsat_files(context, env_vars_fp: str, data_dir: str, metadata_db_fp: str, debug_fp: str, table_id: str, project_id: str, start_date: str='', end_date: str=''):
    _ = dotenv.load_dotenv(env_vars_fp)
    dm = eumetsat.DownloadManager(os.environ.get('USER_KEY'), os.environ.get('USER_SECRET'), data_dir, metadata_db_fp, debug_fp, slack_webhook_url=os.environ.get('SLACK_WEBHOOK_URL'), slack_id=os.environ.get('SLACK_ID'))
    
    missing_datasets = io.identifying_missing_datasets(start_date, end_date)
    df_new_metadata = dm.download_datasets(missing_datasets)
    
    if df_new_metadata is None:
        df_new_metadata = pd.DataFrame(columns=['result_time', 'file_name'])
    else:
        df_new_metadata = df_new_metadata.iloc[1:] # the first entry is the last one we downloaded
    
    return df_new_metadata
```
