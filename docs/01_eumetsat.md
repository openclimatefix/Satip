# EUMETSAT API Wrapper Development



    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  4.31rows/s]
    

<br>

### User Input

```
data_dir = '../data/raw'
compressed_dir = '../data/compressed'
debug_fp = '../logs/EUMETSAT_download.txt'
env_vars_fp = '../.env'
metadata_db_fp = '../data/EUMETSAT_metadata.db'

download_data = True
```

<br>

### Authorising API Access

First we'll load the the environment variables

```
dotenv.load_dotenv(env_vars_fp)

user_key = os.environ.get('USER_KEY')
user_secret = os.environ.get('USER_SECRET')
slack_id = os.environ.get('SLACK_ID')
slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
```

<br>

And test they were loaded successfully

```
def check_env_vars_have_loaded(env_vars):
    for name, value in env_vars.items():
        assert value is not None, f'{name}` should not be None'
    
    return

env_vars = {
    'user_key': user_key,
    'user_secret': user_secret,
    'slack_id': slack_id,
    'slack_webhook_url': slack_webhook_url
}

check_env_vars_have_loaded(env_vars)
```

<br>

We'll then use them to request an access token for the API

<br>

We'll then use them to request an access token for the API

```
access_token = request_access_token(user_key, user_secret)
```

<br>

### Querying Available Data

Before we can download any data we have to know where it's stored. To learn this we can query their search-products API, which returns a JSON containing a list of file metadata.  

Dcumentation for the Swagger API endpoint can be found here: https://eumetsatspace.atlassian.net/wiki/spaces/DSDS/pages/316080237/Swagger+UI+OpenSearch+API  


<br>

We'll quickly make a test request to this end-point

```
start_date = '2019-10-01'
end_date = '2020-10-01'

r = query_data_products(start_date, end_date)

r_json = r.json()
JSON(r_json)
```




    <IPython.core.display.JSON object>



<br>

However the search-api is capped (at 10,000) for the number of files it will return metadata for, so we'll create a while loop that waits until all the relevant data has been returned. We'll then extract just the list of features from the returned JSONs.  

While the search-api returns max 10,000 results, using start-index etc doesn't seem to work for wide time searches, so we will need to do multiple queries.  
Also key to note the results are returned most recent first, so we must proceed backwards in iterations of 10,000  

<br>

We'll check that the same number of available datasets are identified

```
%%time

start_date = '2020-01-01'
end_date = '2020-04-01'
datasets = identify_available_datasets(start_date, end_date)

print(f'{len(datasets)} datasets have been identified')
```

    identify_available_datasets: found 18142 results from API
    18142 datasets have been identified
    CPU times: user 940 ms, sys: 114 ms, total: 1.05 s
    Wall time: 6.2 s
    

```
# JSON(datasets)
```

<br>

Finally we'll create a helper function for converting the dataset ids into their file urls.

<br>

We'll now test this works.

N.b. You cannot use the link returned here directly as it will not be OAuth'ed

```
dataset_ids = sorted([dataset['id'] for dataset in datasets])
example_data_link = dataset_id_to_link(dataset_ids[0])

example_data_link
```




    'https://api.eumetsat.int/data/download/products/MSG2-SEVI-MSG15-0100-NA-20200303090418.826000000Z-NA'



<br>

### Downloading Data

Now that we know where our data is located we want to download it. First we'll check that the directory we wish to save the data in exists, if not we'll create it

```
for folder in [data_dir, compressed_dir]:
    if not os.path.exists(folder):
        os.makedirs(folder)
```

<br>

We also want to extract the relevant metadata information from each file. Here we'll create a generalised framework for extracting data from any product, to add a new one please add its metadata mapping under the relevant `product_id`.

<br>

We're now ready to create a download manager that will handle all of the querying, processing and retrieving for us

<br>

We'll now see what it looks like when we initialise the download manager

```
dm = DownloadManager(user_key, user_secret, data_dir, metadata_db_fp, debug_fp, 
                     slack_webhook_url=slack_webhook_url, slack_id=slack_id)

start_date = '2020-10-01 12:00'
end_date = '2020-10-01 12:05'

if download_data == True:
    dm.download_date_range(start_date, end_date)

df_metadata = dm.get_df_metadata()

df_metadata.head()
```

    2021-03-08 09:48:44,953 - INFO - ********** Download Manager Initialised **************
    2021-03-08 09:48:45,280 - INFO - 1 files queried, 0 found in ../data/raw, 1 to download.
    

    identify_available_datasets: found 1 results from API
    


<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:0; max-width:15ex; vertical-align:middle; text-align:right"></span>
<progress style="width:60ex" max="1" value="0" class="Progress-main"/></progress>
<span class="Progress-label"><strong>0%</strong></span>
<span class="Iteration-label">0/1</span>
<span class="Time-label">[0<0, 0.00s/it]</span></div>


<br>

The `get_size` function was adapted from <a href="https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python">this stackoverflow answer</a>

```
data_dir_size = get_dir_size(data_dir)

print(f'The data directory is currently {round(data_dir_size/1_000_000_000, 2):,} Gb')
```

## Integration with Google Cloud Storage

If Google Cloud Platform (GCP) flags are passed (`bucket_name` and `bucket_prefix`), when downloading, then the `DownloadManager` should first check to see if the files already exist in the specified cloud storage bucket.  
If the files already exist, then they will not be downloaded locally - if the storage bucket arguments are passed.  

```
BUCKET_NAME = "solar-pv-nowcasting-data"
PREFIX = "satellite/EUMETSAT/SEVIRI_RSS/native/2020"
```

```
dm = DownloadManager(user_key, user_secret, data_dir, metadata_db_fp, debug_fp, bucket_name=BUCKET_NAME, bucket_prefix=PREFIX)
```

```
# Bucket filenames can be accessed
len(dm.bucket_filenames)
```

Lets test this by examining some dates at the start of 2020

```
# Timings: around 2 hours to download 1 day.

# DownloadManager should find these 2020 files on the VM
start_date = '2020-01-01 00:00'
end_date = '2020-01-01 00:02'
dm.download_date_range(start_date, end_date)
```

## Name Convention changes in EUMETSAT files

Probably due to the changes / creation of the EUMETSAT API around the end of 2019, newer files do not contain the previous 'order number' parts at the end of the filename. 

Some previously downloaded files follow a different file name convention:

Files through new API:
`MSG3-SEVI-MSG15-0100-NA-20191001120415.883000000Z-NA.nat`  
SatProgram-Instrument-SatNumber-AlgoVersion-InstrumentMode(?)-ReceptionStartDateUTC   

Files on GCP:  
` MSG3-SEVI-MSG15-0100-NA-20191001120415.883000000Z-20191001120433-1399526-1.nat.bz2`  
SatProgram-Instrument-SatNumber-AlgoVersion-InstrumentMode(?)-ReceptionStartDateUTC-SensingStartDateUTC-OrderNumber-PartNumber 

We can use regex to take the first part of the filename for comparisons

```
txt = "MSG3-SEVI-MSG15-0100-NA-20190101000417.314000000Z-20190101000435-1377854-1.nat"
re.match("([A-Z\d.]+-){6}", txt)[0][:-1] # [:-1] to trim the trailing -
```

To ensure we are comparing the same filenames, this regex is added into DownloadManager and the GCP helpers.

Set up logging locally.

```
debug_fp = '../logs/EUMETSAT_download.txt'
log = utils.set_up_logging('EUMETSAT Processing', debug_fp)
```

## Helper utils

For local testing, this command downloads some files from the Google Cloud bucket:

```
# get test files from GCP - these are compressed
# !gsutil cp -r gs://solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/native/2019/10/01/00/04 ../data/raw
```

## Compress downloaded native image files

Once files have been downloaded from the EUMETSAT API in some location, they need to be compressed and saved in a cloud storage bucket. 

First, see which files have already been downloaded locally to test this functionality.  

```
full_native_filenames = glob.glob(os.path.join(data_dir, '*.nat'))
full_native_filenames
```

We will compress locally downloaded files here using `pbzip2`  
On ubuntu: `sudo apt-get install -y pbzip2`  
On mac: `brew install pbzip2`  

```
compress_downloaded_files(data_dir=data_dir, compressed_dir=compressed_dir)
```

## Syncing files to GCP Storage

Compressed native files should be stored in a Google Cloud Storage Bucket. The folder structure follows the following convention:  

`gs://solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/native/<year>/<month>/<day>/<hour>/<minute>/`

```
# sync downloaded files in compressed_dir to the bucket
BUCKET_NAME = "solar-pv-nowcasting-data"
PREFIX = "satellite/EUMETSAT/SEVIRI_RSS/native/"
```
