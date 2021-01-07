# EUMETSAT and GCP 



### Setup

## Some GCP Helpers

First need a couple of helper functions to work with Google Cloud Platform.  
Ideally the principles will transfer easily to other cloud providers if necessary. 

## User input

```python
BUCKET_NAME = "solar-pv-nowcasting-data"
PREFIX = "satellite/EUMETSAT/SEVIRI_RSS/native/2020"
```

```python
blobs = list_blobs_with_prefix(BUCKET_NAME, prefix=PREFIX)
```

```python
print(f'There are {len(blobs)} files')
```

    There are 2 files
    

```python
blobs[:10]
```




    ['satellite/EUMETSAT/SEVIRI_RSS/native/2020/01/01/12/04/MSG3-SEVI-MSG15-0100-NA-20200101120418.186000000Z-NA.nat.bz2',
     'satellite/EUMETSAT/SEVIRI_RSS/native/2020/01/01/12/09/MSG3-SEVI-MSG15-0100-NA-20200101120916.896000000Z-NA.nat.bz2']



```python
storage_client = storage.Client()

PREFIX = "satellite/EUMETSAT/SEVIRI_RSS/native/2018/"

# Note: Client.list_blobs requires at least package version 1.17.0.
blobs_ = storage_client.list_blobs(BUCKET_NAME, prefix=PREFIX)

sizes = []

for blob in blobs_:
    sizes.append(blob.size)
```


    ---------------------------------------------------------------------------

    KeyboardInterrupt                         Traceback (most recent call last)

    <ipython-input-20-8607175daf03> in <module>
          8 sizes = []
          9 
    ---> 10 for blob in blobs_:
         11     sizes.append(blob.size)
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/api_core/page_iterator.py in _items_iter(self)
        210     def _items_iter(self):
        211         """Iterator for each item returned."""
    --> 212         for page in self._page_iter(increment=False):
        213             for item in page:
        214                 self.num_results += 1
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/api_core/page_iterator.py in _page_iter(self, increment)
        247                 self.num_results += page.num_items
        248             yield page
    --> 249             page = self._next_page()
        250 
        251     @abc.abstractmethod
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/api_core/page_iterator.py in _next_page(self)
        367         """
        368         if self._has_next_page():
    --> 369             response = self._get_next_page_response()
        370             items = response.get(self._items_key, ())
        371             page = Page(self, items, self.item_to_value, raw_page=response)
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/api_core/page_iterator.py in _get_next_page_response(self)
        416         params = self._get_query_params()
        417         if self._HTTP_METHOD == "GET":
    --> 418             return self.api_request(
        419                 method=self._HTTP_METHOD, path=self.path, query_params=params
        420             )
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/cloud/storage/_http.py in api_request(self, *args, **kwargs)
         61             if retry:
         62                 call = retry(call)
    ---> 63         return call()
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/api_core/retry.py in retry_wrapped_func(*args, **kwargs)
        279                 self._initial, self._maximum, multiplier=self._multiplier
        280             )
    --> 281             return retry_target(
        282                 target,
        283                 self._predicate,
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/api_core/retry.py in retry_target(target, predicate, sleep_generator, deadline, on_error)
        182     for sleep in sleep_generator:
        183         try:
    --> 184             return target()
        185 
        186         # pylint: disable=broad-except
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/cloud/_http.py in api_request(self, method, path, query_params, data, content_type, headers, api_base_url, api_version, expect_json, _target_object, timeout)
        422             content_type = "application/json"
        423 
    --> 424         response = self._make_request(
        425             method=method,
        426             url=url,
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/cloud/_http.py in _make_request(self, method, url, data, content_type, headers, target_object, timeout)
        286         headers["User-Agent"] = self.user_agent
        287 
    --> 288         return self._do_request(
        289             method, url, headers, data, target_object, timeout=timeout
        290         )
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/cloud/_http.py in _do_request(self, method, url, headers, data, target_object, timeout)
        324         :returns: The HTTP response.
        325         """
    --> 326         return self.http.request(
        327             url=url, method=method, headers=headers, data=data, timeout=timeout
        328         )
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/google/auth/transport/requests.py in request(self, method, url, data, headers, max_allowed_time, timeout, **kwargs)
        462 
        463         with TimeoutGuard(remaining_time) as guard:
    --> 464             response = super(AuthorizedSession, self).request(
        465                 method,
        466                 url,
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/requests/sessions.py in request(self, method, url, params, data, headers, cookies, files, auth, timeout, allow_redirects, proxies, hooks, stream, verify, cert, json)
        540         }
        541         send_kwargs.update(settings)
    --> 542         resp = self.send(prep, **send_kwargs)
        543 
        544         return resp
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/requests/sessions.py in send(self, request, **kwargs)
        695 
        696         if not stream:
    --> 697             r.content
        698 
        699         return r
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/requests/models.py in content(self)
        829                 self._content = None
        830             else:
    --> 831                 self._content = b''.join(self.iter_content(CONTENT_CHUNK_SIZE)) or b''
        832 
        833         self._content_consumed = True
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/requests/models.py in generate()
        751             if hasattr(self.raw, 'stream'):
        752                 try:
    --> 753                     for chunk in self.raw.stream(chunk_size, decode_content=True):
        754                         yield chunk
        755                 except ProtocolError as e:
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/urllib3/response.py in stream(self, amt, decode_content)
        573         else:
        574             while not is_fp_closed(self._fp):
    --> 575                 data = self.read(amt=amt, decode_content=decode_content)
        576 
        577                 if data:
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/urllib3/response.py in read(self, amt, decode_content, cache_content)
        516             else:
        517                 cache_content = False
    --> 518                 data = self._fp.read(amt) if not fp_closed else b""
        519                 if (
        520                     amt != 0 and not data
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/http/client.py in read(self, amt)
        456             # Amount is given, implement using readinto
        457             b = bytearray(amt)
    --> 458             n = self.readinto(b)
        459             return memoryview(b)[:n].tobytes()
        460         else:
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/http/client.py in readinto(self, b)
        500         # connection, and the user is reading more bytes than will be provided
        501         # (for example, reading in 1k chunks)
    --> 502         n = self.fp.readinto(b)
        503         if not n and b:
        504             # Ideally, we would raise IncompleteRead if the content-length
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/socket.py in readinto(self, b)
        667         while True:
        668             try:
    --> 669                 return self._sock.recv_into(b)
        670             except timeout:
        671                 self._timeout_occurred = True
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/ssl.py in recv_into(self, buffer, nbytes, flags)
       1239                   "non-zero flags not allowed in calls to recv_into() on %s" %
       1240                   self.__class__)
    -> 1241             return self.read(nbytes, buffer)
       1242         else:
       1243             return super().recv_into(buffer, nbytes, flags)
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/ssl.py in read(self, len, buffer)
       1097         try:
       1098             if buffer is not None:
    -> 1099                 return self._sslobj.read(len, buffer)
       1100             else:
       1101                 return self._sslobj.read(len)
    

    KeyboardInterrupt: 


```python
sum(sizes) / 1e9
```

2018 contains 2.4TB of data

Note that using the storage client to return blobs returns an iterable of blob metadata objects.  
From those we've extracted the names. We can go backwards from the names to interact with the blobs. 

```python
df = pd.DataFrame(blobs, columns=['blobs'])
df = df[df['blobs'].str.endswith('.nat.bz2')] # only compressed data files
df['datetime'] = pd.to_datetime(df['blobs'].str.slice(start=37, stop=53), format="%Y/%m/%d/%H/%M")
```

```python
months_in_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
```

```python
blobs_by_month = df\
        .assign(year=lambda x: x['datetime'].dt.year)\
        .assign(month=lambda x: x['datetime'].dt.month_name())\
        .groupby(['month', 'year']).count()['blobs'].to_frame()\
        .reset_index()\
        .pivot(index='month', columns='year', values='blobs')\
        .reindex(months_in_order)

blobs_by_month
```




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
      <th>year</th>
      <th>2020</th>
    </tr>
    <tr>
      <th>month</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>January</th>
      <td>2.0</td>
    </tr>
    <tr>
      <th>February</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>March</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>April</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>May</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>June</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>July</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>August</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>September</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>October</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>November</th>
      <td>NaN</td>
    </tr>
    <tr>
      <th>December</th>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>



```python
# credit: https://dfrieds.com/data-visualizations/visualize-historical-time-comparisons.html

figure, axes = plt.subplots(figsize=(10, 11))
sns.heatmap(blobs_by_month, annot=True, linewidths=.5, ax=axes, cmap="Greys")
axes.axes.set_title("Count of .nat.bz files in Storage by Month and Year", fontsize=20, y=1.01)
axes.axes.set_ylabel("month", labelpad=50, rotation=0)
axes.axes.set_xlabel("year", labelpad=16);
plt.yticks(rotation=0);
```

```python
filenames = df['blobs'].str.split('/').str[-1].str.replace('.bz2', '')
```

```python
filenames
```




    1         MSG3-SEVI-MSG15-0100-NA-20180531000417.2340000...
    2         MSG3-SEVI-MSG15-0100-NA-20180531000917.4680000...
    3         MSG3-SEVI-MSG15-0100-NA-20180531001417.7010000...
    4         MSG3-SEVI-MSG15-0100-NA-20180531001917.9350000...
    5         MSG3-SEVI-MSG15-0100-NA-20180531002416.3640000...
                                    ...                        
    170664    MSG3-SEVI-MSG15-0100-NA-20191231233418.2450000...
    170665    MSG3-SEVI-MSG15-0100-NA-20191231233916.9530000...
    170666    MSG3-SEVI-MSG15-0100-NA-20191231234415.6620000...
    170667    MSG3-SEVI-MSG15-0100-NA-20191231234914.3700000...
    170668    MSG3-SEVI-MSG15-0100-NA-20191231235414.2810000...
    Name: blobs, Length: 170667, dtype: object



```python
PREFIX = "satellite/EUMETSAT/SEVIRI_RSS/native/2019/10/01"
filenames = get_eumetsat_filenames(BUCKET_NAME, prefix=PREFIX)
```

```python
len(filenames)
```




    68202



## Write metadata to bigquery

For cloud storage functions, storing metadata in a RDBS seems useful. BigQuery is a low hassle way to achieve this and can scale to lots of data with ease.  
Downsides are rather inflexible migrations and updates.  


```python
# write_metadata_to_gcp(df, 'test', 'solar-pv-nowcasting')
```


    ---------------------------------------------------------------------------

    NotFoundException                         Traceback (most recent call last)

    <ipython-input-29-4f7fbf24d98f> in <module>
    ----> 1 write_metadata_to_gcp(df, 'test', 'solar-pv-nowcasting')
    

    <ipython-input-28-9e358fc4b48b> in write_metadata_to_gcp(df, table_id, project_id, credentials, append)
         13         )
         14     else:
    ---> 15         pandas_gbq.to_gbq(
         16             df,
         17             table_id,
    

    ~/software/anaconda3/envs/satip_dev/lib/python3.8/site-packages/pandas_gbq/gbq.py in to_gbq(dataframe, destination_table, project_id, chunksize, reauth, if_exists, auth_local_webserver, table_schema, location, progress_bar, credentials, verbose, private_key)
       1133 
       1134     if "." not in destination_table:
    -> 1135         raise NotFoundException(
       1136             "Invalid Table Name. Should be of the form 'datasetId.tableId' "
       1137         )
    

    NotFoundException: Invalid Table Name. Should be of the form 'datasetId.tableId' 


    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  1.30rows/s]
    




    '2020-12-03 19:14'


