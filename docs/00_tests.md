# Tests



## setup

```
import os
import dotenv
import json
import pandas as pd
from pandas.util.testing import assert_frame_equal

from satip import eumetsat, io, mario, reproj, usage, utils, gcp_helpers, cicd, backfill
```

Need to set data directories (maybe this should be in a config file)

```
data_dir = '../data/raw'
compressed_dir = '../data/compressed'
debug_fp = '../logs/EUMETSAT_download.txt'
env_vars_fp = '../.env'
metadata_db_fp = '../data/EUMETSAT_metadata.db'
```

Need to load environment variables, as a lot of functionality won't work without some credentials

```
dotenv.load_dotenv(env_vars_fp)

user_key = os.environ.get('USER_KEY')
user_secret = os.environ.get('USER_SECRET')
slack_id = os.environ.get('SLACK_ID')
slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
```

## 01_eumetsat

```
def test_query_data_products():
    """Checks EUMETSAT API 
    
    Looks for a data product from a search query, but does not check details.
    Expects to find one value in the time range.
    """
    start_date = '2019-10-01T00:00:00'
    end_date = '2019-10-01T00:05:00'

    actual = eumetsat.query_data_products(start_date, end_date).json()
    a_id = actual['type']
    a_results = actual['properties']['totalResults']
    assert a_id == 'FeatureCollection'
    assert a_results == 1
```

```
def test_identify_available_datasets():
    """Checks count of available datasets for a timeframe is consistent"""
    start_date = '2020-01-01'
    end_date = '2020-02-01'
    actual = len(eumetsat.identify_available_datasets(start_date, end_date))
    expected = 1548
    assert actual == expected
```

```
def test_DownloadManager_download(user_key, user_secret, data_dir, metadata_db_fp, debug_fp):
    """Downloads 1 file from the EUMETSAT API and compares with saved data. 
    
    Drops the 'downloaded' column which varies based on time of last download.
    """
    dm = eumetsat.DownloadManager(user_key, user_secret, data_dir, metadata_db_fp, debug_fp)
    start_date = '2020-10-01 12:00'
    end_date = '2020-10-01 12:05'
    
    actual = dm.download_date_range(start_date, end_date).drop('downloaded', axis=1)
    expected = pd.DataFrame(data=[[pd.Timestamp('2020-10-01 12:00:09.607000+0000', tz='UTC'), pd.Timestamp('2020-10-01 12:04:15.953000+0000', tz='UTC'), pd.Timestamp('2020-10-01 12:04:15.953000+0000', tz='UTC'), 'MSG3', 'GEO', 'SEVIRI', 'RSS', 'EPSG:4326', '0 9.5', 'MSG3-SEVI-MSG15-0100-NA-20201001120415.953000000Z-NA', 99819, 0.0]], 
                            columns=['start_date', 'end_date', 'result_time', 'platform_short_name','platform_orbit_type', 'instrument_name', 'sensor_op_mode', 'center_srs_name', 'center_position', 'file_name', 'file_size', 'missing_pct'])
    
    assert_frame_equal(actual, expected)
```

### Export
