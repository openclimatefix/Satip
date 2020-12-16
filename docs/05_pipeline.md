# End-to-End Pipeline



```python
#exports
import pandas as pd
import xarray as xr

from satip import eumetsat, reproj, io, gcp_helpers
from dagster import execute_pipeline, pipeline, solid, Field

import os
import dotenv
```

    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\google\auth\_default.py:69: UserWarning: Your application has authenticated using end user credentials from Google Cloud SDK without a quota project. You might receive a "quota exceeded" or "API not enabled" error. We recommend you rerun `gcloud auth application-default login` and make sure a quota project is added. Or you can use service accounts instead. For more information about service accounts, see https://cloud.google.com/docs/authentication/
      warnings.warn(_CLOUD_SDK_CREDENTIALS_WARNING)
    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  3.21rows/s]
    

<br>

### User Inputs

```python
data_dir = '../data/raw'
sorted_dir = '../data/sorted'
debug_fp = '../logs/EUMETSAT_download.txt'
env_vars_fp = '../.env'
metadata_db_fp = '../data/EUMETSAT_metadata.db'
new_grid_fp='../data/intermediate/new_grid_4km_TM.json'
new_coords_fp = '../data/intermediate/reproj_coords_TM_4km.csv'
zarr_bucket = 'solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/full_extent_TM_int16'
```

<br>

### Loading Environment Variables

```python
#exports
dotenv.load_dotenv(env_vars_fp)

user_key = os.environ.get('USER_KEY')
user_secret = os.environ.get('USER_SECRET')
slack_id = os.environ.get('SLACK_ID')
slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
```

<br>

### Dagster Pipeline

We're now going to combine these steps into a pipeline using `dagster`

```python
@solid(
    config_schema = {
        'user_key': Field(str, default_value=user_key, is_required=False),
        'user_secret': Field(str, default_value=user_secret, is_required=False),
        'slack_webhook_url': Field(str, default_value=slack_webhook_url, is_required=False),
        'slack_id': Field(str, default_value=slack_id, is_required=False)
    }
)
def download_latest_eumetsat_files(context, data_dir: str, metadata_db_fp: str, debug_fp: str, start_date: str=''):
    if start_date == '':
        sql_query = f'select * from {table_id} where result_time = (select max(result_time) from {table_id})'
        start_date = gcp_helpers.query(sql_query, project_id)['result_time'].iloc[0]
        
    end_date = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')

    dm = eumetsat.DownloadManager(context.solid_config['user_key'], context.solid_config['user_secret'], data_dir, metadata_db_fp, debug_fp, slack_webhook_url=context.solid_config['slack_webhook_url'], slack_id=context.solid_config['slack_id'])
    df_new_metadata = dm.download_datasets(start_date, end_date)

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
def save_metadata(_, df_new_metadata, table_id: str, project_id: str):
    gcp_helpers.write_metadata_to_gcp(df_new_metadata, table_id, project_id, append=True)
```

```python
@pipeline
def download_latest_data_pipeline():  
    # Retrieving data, reprojecting, compressing, and saving to GCP
    df_new_metadata = download_latest_eumetsat_files()
    datetime_to_filepath = df_metadata_to_dt_to_fp_map(df_new_metadata)
    ds_combined_reproj = reproject_datasets(datetime_to_filepath)
    ds_combined_compressed = compress_and_save_datasets(ds_combined_reproj)
    save_metadata(df_new_metadata)
```

```python
run_config = {
    'solids': {
        'download_latest_eumetsat_files': {
            'inputs': {
                'data_dir': "../data/raw",
                'metadata_db_fp': "../data/EUMETSAT_metadata.db",
                'debug_fp': "../logs/EUMETSAT_download.txt",
                'start_date': "2020-12-16 19:30"
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
        }
    }
}

execute_pipeline(download_latest_data_pipeline, run_config=run_config)
```

    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - ENGINE_EVENT - Starting initialization of resources [asset_store].
    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - ENGINE_EVENT - Finished initialization of resources [asset_store].
    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - PIPELINE_START - Started execution of pipeline "download_latest_data_pipeline".
    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - ENGINE_EVENT - Executing steps in process (pid: 20040)
    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - download_latest_eumetsat_files.compute - STEP_START - Started execution of step "download_latest_eumetsat_files.compute".
    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - download_latest_eumetsat_files.compute - STEP_INPUT - Got input "data_dir" of type "String". (Type check passed).
    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - download_latest_eumetsat_files.compute - STEP_INPUT - Got input "metadata_db_fp" of type "String". (Type check passed).
    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - download_latest_eumetsat_files.compute - STEP_INPUT - Got input "debug_fp" of type "String". (Type check passed).
    2020-12-16 20:00:18 - dagster - DEBUG - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - download_latest_eumetsat_files.compute - STEP_INPUT - Got input "start_date" of type "String". (Type check passed).
    2020-12-16 20:00:19 - dagster - ERROR - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - download_latest_eumetsat_files.compute - STEP_FAILURE - Execution of step "download_latest_eumetsat_files.compute" failed.
    
    AttributeError: 'DagsterLogManager' object has no attribute 'setLevel'
    
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
      File "<ipython-input-5-968917ba6d74>", line 16, in download_latest_eumetsat_files
        dm = eumetsat.DownloadManager(context.solid_config['user_key'], context.solid_config['user_secret'], data_dir, metadata_db_fp, debug_fp, slack_webhook_url=context.solid_config['slack_webhook_url'], slack_id=context.solid_config['slack_id'], logger_name=context.log)
      File "c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\eumetsat.py", line 312, in __init__
        self.logger = utils.set_up_logging(logger_name, log_fp,
      File "c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\utils.py", line 133, in set_up_logging
        logger.setLevel(getattr(logging, main_logging_level))
    
    2020-12-16 20:00:19 - dagster - ERROR - download_latest_data_pipeline - 843966a6-a689-430d-97e0-7c937aefc85e - 20040 - PIPELINE_FAILURE - Execution of pipeline "download_latest_data_pipeline" failed. An exception was thrown during execution.
    
    AttributeError: 'DagsterLogManager' object has no attribute 'setLevel'
    
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
      File "<ipython-input-5-968917ba6d74>", line 16, in download_latest_eumetsat_files
        dm = eumetsat.DownloadManager(context.solid_config['user_key'], context.solid_config['user_secret'], data_dir, metadata_db_fp, debug_fp, slack_webhook_url=context.solid_config['slack_webhook_url'], slack_id=context.solid_config['slack_id'], logger_name=context.log)
      File "c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\eumetsat.py", line 312, in __init__
        self.logger = utils.set_up_logging(logger_name, log_fp,
      File "c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\utils.py", line 133, in set_up_logging
        logger.setLevel(getattr(logging, main_logging_level))
    
    


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
            step key: "download_latest_eumetsat_files.compute"
            solid invocation: "download_latest_eumetsat_files"
            solid definition: "download_latest_eumetsat_files"
            

    
    During handling of the above exception, another exception occurred:
    

    AttributeError                            Traceback (most recent call last)

        [... skipping hidden 1 frame]
    

    <ipython-input-7-79fdcc951128> in <module>
         36 
    ---> 37 execute_pipeline(download_latest_data_pipeline, run_config=run_config)
    

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
    

    <ipython-input-5-968917ba6d74> in download_latest_eumetsat_files(context, data_dir, metadata_db_fp, debug_fp, start_date)
         15 
    ---> 16     dm = eumetsat.DownloadManager(context.solid_config['user_key'], context.solid_config['user_secret'], data_dir, metadata_db_fp, debug_fp, slack_webhook_url=context.solid_config['slack_webhook_url'], slack_id=context.solid_config['slack_id'], logger_name=context.log)
         17     df_new_metadata = dm.download_datasets(start_date, end_date)
    

    c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\eumetsat.py in __init__(self, user_key, user_secret, data_dir, metadata_db_fp, log_fp, main_logging_level, slack_logging_level, slack_webhook_url, slack_id, bucket_name, bucket_prefix, logger_name)
        311         # Configuring the logger
    --> 312         self.logger = utils.set_up_logging(logger_name, log_fp,
        313                                            main_logging_level, slack_logging_level,
    

    c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\utils.py in set_up_logging(name, log_dir, main_logging_level, slack_logging_level, slack_webhook_url, slack_id)
        132 
    --> 133     logger.setLevel(getattr(logging, main_logging_level))
        134 
    

    AttributeError: 'DagsterLogManager' object has no attribute 'setLevel'

    
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
            step key: "download_latest_eumetsat_files.compute"
            solid invocation: "download_latest_eumetsat_files"
            solid definition: "download_latest_eumetsat_files"
            

    
    During handling of the above exception, another exception occurred:
    

    AttributeError                            Traceback (most recent call last)

    <ipython-input-7-79fdcc951128> in <module>
         35 }
         36 
    ---> 37 execute_pipeline(download_latest_data_pipeline, run_config=run_config)
    

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
    

    <ipython-input-5-968917ba6d74> in download_latest_eumetsat_files(context, data_dir, metadata_db_fp, debug_fp, start_date)
         14     end_date = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
         15 
    ---> 16     dm = eumetsat.DownloadManager(context.solid_config['user_key'], context.solid_config['user_secret'], data_dir, metadata_db_fp, debug_fp, slack_webhook_url=context.solid_config['slack_webhook_url'], slack_id=context.solid_config['slack_id'], logger_name=context.log)
         17     df_new_metadata = dm.download_datasets(start_date, end_date)
         18 
    

    c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\eumetsat.py in __init__(self, user_key, user_secret, data_dir, metadata_db_fp, log_fp, main_logging_level, slack_logging_level, slack_webhook_url, slack_id, bucket_name, bucket_prefix, logger_name)
        310 
        311         # Configuring the logger
    --> 312         self.logger = utils.set_up_logging(logger_name, log_fp,
        313                                            main_logging_level, slack_logging_level,
        314                                            slack_webhook_url, slack_id)
    

    c:\users\ayrto\desktop\freelance work\fea\work\ocf\satip\satip\utils.py in set_up_logging(name, log_dir, main_logging_level, slack_logging_level, slack_webhook_url, slack_id)
        131     assert slack_logging_level in logging_levels, f"slack_logging_level must be one of {', '.join(logging_levels)}"
        132 
    --> 133     logger.setLevel(getattr(logging, main_logging_level))
        134 
        135     # Defining global formatter
    

    AttributeError: 'DagsterLogManager' object has no attribute 'setLevel'

