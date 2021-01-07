# EUMETSAT API Wrapper Development

<br>

### User Input

```python
data_dir = '../data/raw'
sorted_dir = '../data/sorted'
debug_fp = '../logs/EUMETSAT_download.txt'
env_vars_fp = '../.env'
metadata_db_fp = '../data/EUMETSAT_metadata.db'

download_data = True
```

<br>

### Authorising API Access

First we'll load the the environment variables

```python
dotenv.load_dotenv(env_vars_fp)

user_key = os.environ.get('USER_KEY')
user_secret = os.environ.get('USER_SECRET')
slack_id = os.environ.get('SLACK_ID')
slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
```

<br>

And test they were loaded successfully

```python
def check_env_vars_have_loaded(env_vars):
    for name, value in env_vars.items():
        assert value is not None, f'{name}` should not be None'

    return

env_vars = {
    'user_key': user_key,
    'user_secret': user_secret,
}

check_env_vars_have_loaded(env_vars)
```

<br>

We'll then use them to request an access token for the API

<br>

We'll then use them to request an access token for the API

```python
access_token = request_access_token(user_key, user_secret)
```

<br>

### Querying Available Data

Before we can download any data we have to know where it's stored. To learn this we can query their search-products API, which returns a JSON containing a list of file metadata.

<br>

We'll quickly make a test request to this end-point

```python
start_date = '2019-10-01'
end_date = '2019-10-07'

r = query_data_products(start_date, end_date)

r_json = r.json()
```

<br>

However the search-api is capped (at 10,000) for the number of files it will return metadata for, so we'll create a while loop that waits until all the relevant data has been returned. We'll then extract just the list of features from the returned JSONs.

<br>

We'll check that the same number of available datasets are identified

```python
%%time

datasets = identify_available_datasets(start_date, end_date)

print(f'{len(datasets)} datasets have been identified')
```

    1728 datasets have been identified
    Wall time: 1.19 s

<br>

Finally we'll create a helper function for converting the dataset ids into their file urls.

<br>

We'll now test this works.

N.b. You cannot use the link returned here directly as it will not be OAuth'ed

```python
dataset_ids = sorted([dataset['id'] for dataset in datasets])
example_data_link = dataset_id_to_link(dataset_ids[0])

example_data_link
```

    'https://api.eumetsat.int/data/download/products/MSG3-SEVI-MSG15-0100-NA-20191001000415.000000000Z-NA'

<br>

### Downloading Data

Now that we know where our data is located we want to download it. First we'll check that the directory we wish to save the data in exists, if not we'll create it

```python
for folder in [data_dir, sorted_dir]:
    if not os.path.exists(folder):
        os.makedirs(folder)
```

<br>

We also want to extract the relevant metadata information from each file. Here we'll create a generalised framework for extracting data from any product, to add a new one please add its metadata mapping under the relevant `product_id`.

<br>

We're now ready to create a download manager that will handle all of the querying, processing and retrieving for us

<br>

We'll now see what it looks like when we initialise the download manager

```python
dm = DownloadManager(user_key, user_secret, data_dir, metadata_db_fp, debug_fp,
                     slack_webhook_url=slack_webhook_url, slack_id=slack_id)

start_date = '2020-10-01 12:00'
end_date = '2020-10-01 12:05'

if download_data == True:
    dm.download_date_range(start_date, end_date)

df_metadata = dm.get_df_metadata()

df_metadata.head()
```

    2020-12-16 23:12:02,565 - INFO - ********** Download Manager Initialised **************
    2020-12-16 23:12:03,112 - INFO - 1 files queried, 1 found in ../data/raw, 0 to download.
    2020-12-16 23:12:03,115 - INFO - No files will be downloaded. Set DownloadManager bucket_name argument for local download

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }

</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>start_date</th>
      <th>end_date</th>
      <th>result_time</th>
      <th>platform_short_name</th>
      <th>platform_orbit_type</th>
      <th>instrument_name</th>
      <th>sensor_op_mode</th>
      <th>center_srs_name</th>
      <th>center_position</th>
      <th>file_name</th>
      <th>file_size</th>
      <th>missing_pct</th>
      <th>downloaded</th>
    </tr>
    <tr>
      <th>id</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>1</th>
      <td>2020-10-01 12:05:09.428</td>
      <td>2020-10-01 12:09:15.775</td>
      <td>2020-10-01 12:09:15.775</td>
      <td>MSG3</td>
      <td>GEO</td>
      <td>SEVIRI</td>
      <td>RSS</td>
      <td>EPSG:4326</td>
      <td>0 9.5</td>
      <td>MSG3-SEVI-MSG15-0100-NA-20201001120915.7750000...</td>
      <td>99819</td>
      <td>0.0</td>
      <td>2020-11-13 10:32:40.853958</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2020-10-01 12:10:09.249</td>
      <td>2020-10-01 12:14:15.596</td>
      <td>2020-10-01 12:14:15.596</td>
      <td>MSG3</td>
      <td>GEO</td>
      <td>SEVIRI</td>
      <td>RSS</td>
      <td>EPSG:4326</td>
      <td>0 9.5</td>
      <td>MSG3-SEVI-MSG15-0100-NA-20201001121415.5960000...</td>
      <td>99819</td>
      <td>0.0</td>
      <td>2020-11-13 10:32:56.874131</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2020-10-01 12:15:09.071</td>
      <td>2020-10-01 12:19:15.417</td>
      <td>2020-10-01 12:19:15.417</td>
      <td>MSG3</td>
      <td>GEO</td>
      <td>SEVIRI</td>
      <td>RSS</td>
      <td>EPSG:4326</td>
      <td>0 9.5</td>
      <td>MSG3-SEVI-MSG15-0100-NA-20201001121915.4170000...</td>
      <td>99819</td>
      <td>0.0</td>
      <td>2020-11-13 10:33:13.998136</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2020-10-01 12:20:08.892</td>
      <td>2020-10-01 12:24:15.239</td>
      <td>2020-10-01 12:24:15.239</td>
      <td>MSG3</td>
      <td>GEO</td>
      <td>SEVIRI</td>
      <td>RSS</td>
      <td>EPSG:4326</td>
      <td>0 9.5</td>
      <td>MSG3-SEVI-MSG15-0100-NA-20201001122415.2390000...</td>
      <td>99819</td>
      <td>0.0</td>
      <td>2020-11-13 10:33:30.656217</td>
    </tr>
    <tr>
      <th>5</th>
      <td>2020-10-01 12:25:08.714</td>
      <td>2020-10-01 12:29:15.060</td>
      <td>2020-10-01 12:29:15.060</td>
      <td>MSG3</td>
      <td>GEO</td>
      <td>SEVIRI</td>
      <td>RSS</td>
      <td>EPSG:4326</td>
      <td>0 9.5</td>
      <td>MSG3-SEVI-MSG15-0100-NA-20201001122915.0600000...</td>
      <td>99819</td>
      <td>0.0</td>
      <td>2020-11-13 10:33:46.352754</td>
    </tr>
  </tbody>
</table>
</div>

<br>

The `get_size` function was adapted from <a href="https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python">this stackoverflow answer</a>

```python
data_dir_size = get_dir_size(data_dir)

print(f'The data directory is currently {round(data_dir_size/1_000_000_000, 2):,} Gb')
```

    The data directory is currently 30.36 Gb

<br>
<br>
<br>
<br>

# Need to Clean Notebook Below Here

<br>
<br>
<br>
<br>

## Trying out bucket files

If GCP flags are passed (`bucket_name` and `bucket_prefix`), when downloading the `DownloadManager` should first check to see if the files already exist in the specified bucket.  
If the files already exist, then don't download them.

```python
BUCKET_NAME = "solar-pv-nowcasting-data"
PREFIX = "satellite/EUMETSAT/SEVIRI_RSS/native/2020"
```

```python
dm = DownloadManager(user_key, user_secret, data_dir, metadata_db_fp, debug_fp, bucket_name=BUCKET_NAME, bucket_prefix=PREFIX)
```

    2020-11-30 10:21:30,271 - INFO - ********** Download Manager Initialised **************


    Checking files in GCP bucket solar-pv-nowcasting-data, this will take a few seconds

```python
len(dm.bucket_filenames)
```

    2

```python
%time # took around 2 hours to download 1 day.

# DownloadManager should find these 2019 files on the VM
start_date = '2020-01-01 00:00'
end_date = '2020-01-02 00:00'
dm.download_date_range(start_date, end_date)
```

    CPU times: user 3 Âµs, sys: 1 Âµs, total: 4 Âµs
    Wall time: 6.2 Âµs


    2020-11-30 10:22:42,304 - INFO - 288 files queried, 2 found in bucket, 0 found in ../data/raw, 286 to download.

<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:0; max-width:15ex; vertical-align:middle; text-align:right"></span>
<progress style="width:60ex" max="286" value="286" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">286/286</span>
<span class="Time-label">[02:08:45<00:22, 27.01s/it]</span></div>

    2020-11-30 11:31:58,945 - INFO - The EUMETSAT access token has been refreshed

However, the already downloaded files follow a different file name convention.

Files through new API:
`MSG3-SEVI-MSG15-0100-NA-20191001120415.883000000Z-NA.nat`  
SatProgram-Instrument-SatNumber-AlgoVersion-InstrumentMode(?)-ReceptionStartDateUTC

Files on GCP:  
` MSG3-SEVI-MSG15-0100-NA-20191001120415.883000000Z-20191001120433-1399526-1.nat.bz2`  
SatProgram-Instrument-SatNumber-AlgoVersion-InstrumentMode(?)-ReceptionStartDateUTC-SensingStartDateUTC-OrderNumber-PartNumber

Let's have a look at the filename lengths.

```python
filenames = pd.DataFrame(dm.bucket_filenames, columns=['filenames'])
filenames['length'] = filenames['filenames'].str.len()
filenames.groupby('length').count()
```

```python
print(filenames.loc[0].filenames)
print(filenames.loc[102460].filenames)
```

Looks like the length difference is just due to the `part number` at the end of the filename

We can use regex to take the first part of the filename for comparisons

```python
txt = "MSG3-SEVI-MSG15-0100-NA-20190101000417.314000000Z-20190101000435-1377854-1.nat"
re.match("([A-Z\d.]+-){6}", txt)[0][:-1] # [:-1] to trim the trailing -
```

Now we're comparing the same filenames by adding this regex into DownloadManager and the GCP helpers.

## Logging

```python
debug_fp = '../logs/EUMETSAT_download.txt'
log = utils.set_up_logging('EUMETSAT Processing', debug_fp)
```

## Helper utils

## Download files from GCP

```python
# get test files from GCP - these are compressed
# !gsutil cp -r gs://solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/native/2019/10/01/00/04 ../data/raw
```

## Compress and move files

```python
full_native_filenames = glob.glob(os.path.join(data_dir, '*.nat'))
```

```python
full_native_filenames
```

    []

We will compress locally downloaded files here using `pbzip2`  
On ubuntu: `sudo apt-get install -y pbzip2`  
On mac: `brew install pbzip2`

```python
compress_downloaded_files(data_dir=data_dir, sorted_dir=sorted_dir)
```

    2020-11-29 22:10:05,805 - INFO - Found 0 native files.


    Found 0 native files.

## Sync to GCP Storage

`store the bzip2 in gs://solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/native/<year>/<month>/<day>/<hour>/<minute>/`

```python
# sync downloaded files in sorted_dir to the bucket
BUCKET_NAME = "solar-pv-nowcasting-data"
PREFIX = "satellite/EUMETSAT/SEVIRI_RSS/native/"
```
