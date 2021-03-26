# Zarr




<br>

### Imports

    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\google\auth\_default.py:69: UserWarning: Your application has authenticated using end user credentials from Google Cloud SDK without a quota project. You might receive a "quota exceeded" or "API not enabled" error. We recommend you rerun `gcloud auth application-default login` and make sure a quota project is added. Or you can use service accounts instead. For more information about service accounts, see https://cloud.google.com/docs/authentication/
      warnings.warn(_CLOUD_SDK_CREDENTIALS_WARNING)
    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  1.28rows/s]
    

```python
import os
import dotenv

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from IPython.display import JSON
```

<br>

### User Inputs

```python
data_dir = '../data/raw'
metadata_db_fp = '../data/EUMETSAT_metadata.db'
debug_fp = '../logs/EUMETSAT_download.txt'
new_grid_fp='../data/intermediate/new_grid_4km_TM.json'
new_coords_fp = '../data/intermediate/reproj_coords_TM_4km.csv'

in_zarr_bucket = 'solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/OSGB36/all_zarr'
out_zarr_bucket = 'solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/full_extent_TM_int16'
```

<br>

### Loading Environment Variables

```python
dotenv.load_dotenv('../.env')

user_key = os.environ.get('USER_KEY')
user_secret = os.environ.get('USER_SECRET')
slack_id = os.environ.get('SLACK_ID')
slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
```

<br>

### Preparing Data to Save to Zarr

We'll start by loading in one of the datasets we've just downloaded, in this instance we'll take the most recent one by identifying it from the metadata db.

```python
dm = eumetsat.DownloadManager(user_key, user_secret, data_dir, metadata_db_fp, debug_fp)

df_metadata = dm.get_df_metadata()

df_metadata.tail()
```

    2021-03-19 13:36:06,283 - INFO - ********** Download Manager Initialised **************
    




|   ('Unnamed: 0_level_0', 'id') | ('start_date', 'Unnamed: 1_level_1')   | ('end_date', 'Unnamed: 2_level_1')   | ('result_time', 'Unnamed: 3_level_1')   | ('platform_short_name', 'Unnamed: 4_level_1')   | ('platform_orbit_type', 'Unnamed: 5_level_1')   | ('instrument_name', 'Unnamed: 6_level_1')   | ('sensor_op_mode', 'Unnamed: 7_level_1')   | ('center_srs_name', 'Unnamed: 8_level_1')   | ('center_position', 'Unnamed: 9_level_1')   | ('file_name', 'Unnamed: 10_level_1')              |   ('file_size', 'Unnamed: 11_level_1') |   ('missing_pct', 'Unnamed: 12_level_1') | ('downloaded', 'Unnamed: 13_level_1')   |
|-------------------------------:|:---------------------------------------|:-------------------------------------|:----------------------------------------|:------------------------------------------------|:------------------------------------------------|:--------------------------------------------|:-------------------------------------------|:--------------------------------------------|:--------------------------------------------|:--------------------------------------------------|---------------------------------------:|-----------------------------------------:|:----------------------------------------|
|                             22 | 2021-03-19 13:00:09.714                | 2021-03-19 13:04:16.088              | 2021-03-19 13:04:16.088                 | MSG3                                            | GEO                                             | SEVIRI                                      | RSS                                        | EPSG:4326                                   | 0 9.5                                       | MSG3-SEVI-MSG15-0100-NA-20210319130416.0880000... |                                  99819 |                                       59 | 2021-03-19 13:32:31.390670              |
|                             23 | 2021-03-19 13:05:09.569                | 2021-03-19 13:09:15.943              | 2021-03-19 13:09:15.943                 | MSG3                                            | GEO                                             | SEVIRI                                      | RSS                                        | EPSG:4326                                   | 0 9.5                                       | MSG3-SEVI-MSG15-0100-NA-20210319130915.9430000... |                                  99819 |                                        0 | 2021-03-19 13:32:36.178702              |
|                             24 | 2021-03-19 13:10:09.423                | 2021-03-19 13:14:15.798              | 2021-03-19 13:14:15.798                 | MSG3                                            | GEO                                             | SEVIRI                                      | RSS                                        | EPSG:4326                                   | 0 9.5                                       | MSG3-SEVI-MSG15-0100-NA-20210319131415.7980000... |                                  99819 |                                        0 | 2021-03-19 13:32:40.347753              |
|                             25 | 2021-03-19 13:15:09.278                | 2021-03-19 13:19:15.652              | 2021-03-19 13:19:15.652                 | MSG3                                            | GEO                                             | SEVIRI                                      | RSS                                        | EPSG:4326                                   | 0 9.5                                       | MSG3-SEVI-MSG15-0100-NA-20210319131915.6520000... |                                  99819 |                                       62 | 2021-03-19 13:32:44.720295              |
|                             26 | 2021-03-19 13:20:10.335                | 2021-03-19 13:24:16.708              | 2021-03-19 13:24:16.708                 | MSG3                                            | GEO                                             | SEVIRI                                      | RSS                                        | EPSG:4326                                   | 0 9.5                                       | MSG3-SEVI-MSG15-0100-NA-20210319132416.7080000... |                                  99819 |                                        0 | 2021-03-19 13:32:48.922629              |</div>



<br>

We'll then load in the file

```python
filename = df_metadata.loc[df_metadata.index[-2], 'file_name']
native_fp = f'{data_dir}/{filename}.nat'

severi_area_def = reproj.get_seviri_area_def(native_fp)
seviri_crs = severi_area_def.to_cartopy_crs()

scene = reproj.load_scene(native_fp)
scene.load(['HRV'])
```

    /Users/laurence/conda/envs/satip_dev/lib/python3.8/site-packages/pyproj/crs/crs.py:543: UserWarning: You will likely lose important projection information when converting to a PROJ string from another format. See: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems
      proj_string = self.to_proj4()
    /Users/laurence/conda/envs/satip_dev/lib/python3.8/site-packages/pyproj/crs/crs.py:543: UserWarning: You will likely lose important projection information when converting to a PROJ string from another format. See: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems
      proj_string = self.to_proj4()
    

<br>

And visualise it to test that everything is working

```python
fig = plt.figure(dpi=250, figsize=(10, 10))
ax = plt.axes(projection=seviri_crs)

scene['HRV'].plot.imshow(ax=ax, cmap='magma', vmin=0, vmax=50)

ax.coastlines(resolution='50m', alpha=0.8, color='white')
```




    <cartopy.mpl.feature_artist.FeatureArtist at 0x7fc2c8619880>




![png](img/nbs/output_12_1.png)


<br>

We now need to reproject it

```python
%%capture --no-stdout
%%time

reprojector = reproj.Reprojector(new_coords_fp, new_grid_fp)
ds_reproj = reprojector.reproject(native_fp, reproj_library='pyresample')
```

    CPU times: user 2.23 s, sys: 104 ms, total: 2.33 s
    Wall time: 2.38 s
    

<br>

Which again we'll check through visualisation

```python
fig = plt.figure(dpi=250, figsize=(10, 10))
ax = plt.axes(projection=ccrs.TransverseMercator())

ds_reproj['stacked_eumetsat_data'].sel(variable='HRV').plot.imshow(ax=ax, cmap='magma', vmin=0, vmax=50)

ax.coastlines(resolution='50m', alpha=0.8, color='white')
```

    <ipython-input-10-53f177b0781d>:2: UserWarning: The default value for the *approx* keyword argument to TransverseMercator will change from True to False after 0.18.
      ax = plt.axes(projection=ccrs.TransverseMercator())
    /Users/laurence/conda/envs/satip_dev/lib/python3.8/site-packages/dask/core.py:121: RuntimeWarning: invalid value encountered in sin
      return func(*(_execute_task(a, cache) for a in args))
    /Users/laurence/conda/envs/satip_dev/lib/python3.8/site-packages/dask/core.py:121: RuntimeWarning: invalid value encountered in cos
      return func(*(_execute_task(a, cache) for a in args))
    




    <cartopy.mpl.feature_artist.FeatureArtist at 0x7fc2c86dd9a0>




![png](img/nbs/output_16_2.png)


```python
ds_reproj['stacked_eumetsat_data']
```




<div><svg style="position: absolute; width: 0; height: 0; overflow: hidden">
<defs>
<symbol id="icon-database" viewBox="0 0 32 32">
<path d="M16 0c-8.837 0-16 2.239-16 5v4c0 2.761 7.163 5 16 5s16-2.239 16-5v-4c0-2.761-7.163-5-16-5z"></path>
<path d="M16 17c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
<path d="M16 26c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
</symbol>
<symbol id="icon-file-text2" viewBox="0 0 32 32">
<path d="M28.681 7.159c-0.694-0.947-1.662-2.053-2.724-3.116s-2.169-2.030-3.116-2.724c-1.612-1.182-2.393-1.319-2.841-1.319h-15.5c-1.378 0-2.5 1.121-2.5 2.5v27c0 1.378 1.122 2.5 2.5 2.5h23c1.378 0 2.5-1.122 2.5-2.5v-19.5c0-0.448-0.137-1.23-1.319-2.841zM24.543 5.457c0.959 0.959 1.712 1.825 2.268 2.543h-4.811v-4.811c0.718 0.556 1.584 1.309 2.543 2.268zM28 29.5c0 0.271-0.229 0.5-0.5 0.5h-23c-0.271 0-0.5-0.229-0.5-0.5v-27c0-0.271 0.229-0.5 0.5-0.5 0 0 15.499-0 15.5 0v7c0 0.552 0.448 1 1 1h7v19.5z"></path>
<path d="M23 26h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
<path d="M23 22h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
<path d="M23 18h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
</symbol>
</defs>
</svg>
<style>/* CSS stylesheet for displaying xarray objects in jupyterlab.
 *
 */

:root {
  --xr-font-color0: var(--jp-content-font-color0, rgba(0, 0, 0, 1));
  --xr-font-color2: var(--jp-content-font-color2, rgba(0, 0, 0, 0.54));
  --xr-font-color3: var(--jp-content-font-color3, rgba(0, 0, 0, 0.38));
  --xr-border-color: var(--jp-border-color2, #e0e0e0);
  --xr-disabled-color: var(--jp-layout-color3, #bdbdbd);
  --xr-background-color: var(--jp-layout-color0, white);
  --xr-background-color-row-even: var(--jp-layout-color1, white);
  --xr-background-color-row-odd: var(--jp-layout-color2, #eeeeee);
}

html[theme=dark],
body.vscode-dark {
  --xr-font-color0: rgba(255, 255, 255, 1);
  --xr-font-color2: rgba(255, 255, 255, 0.54);
  --xr-font-color3: rgba(255, 255, 255, 0.38);
  --xr-border-color: #1F1F1F;
  --xr-disabled-color: #515151;
  --xr-background-color: #111111;
  --xr-background-color-row-even: #111111;
  --xr-background-color-row-odd: #313131;
}

.xr-wrap {
  display: block;
  min-width: 300px;
  max-width: 700px;
}

.xr-text-repr-fallback {
  /* fallback to plain text repr when CSS is not injected (untrusted notebook) */
  display: none;
}

.xr-header {
  padding-top: 6px;
  padding-bottom: 6px;
  margin-bottom: 4px;
  border-bottom: solid 1px var(--xr-border-color);
}

.xr-header > div,
.xr-header > ul {
  display: inline;
  margin-top: 0;
  margin-bottom: 0;
}

.xr-obj-type,
.xr-array-name {
  margin-left: 2px;
  margin-right: 10px;
}

.xr-obj-type {
  color: var(--xr-font-color2);
}

.xr-sections {
  padding-left: 0 !important;
  display: grid;
  grid-template-columns: 150px auto auto 1fr 20px 20px;
}

.xr-section-item {
  display: contents;
}

.xr-section-item input {
  display: none;
}

.xr-section-item input + label {
  color: var(--xr-disabled-color);
}

.xr-section-item input:enabled + label {
  cursor: pointer;
  color: var(--xr-font-color2);
}

.xr-section-item input:enabled + label:hover {
  color: var(--xr-font-color0);
}

.xr-section-summary {
  grid-column: 1;
  color: var(--xr-font-color2);
  font-weight: 500;
}

.xr-section-summary > span {
  display: inline-block;
  padding-left: 0.5em;
}

.xr-section-summary-in:disabled + label {
  color: var(--xr-font-color2);
}

.xr-section-summary-in + label:before {
  display: inline-block;
  content: 'â–º';
  font-size: 11px;
  width: 15px;
  text-align: center;
}

.xr-section-summary-in:disabled + label:before {
  color: var(--xr-disabled-color);
}

.xr-section-summary-in:checked + label:before {
  content: 'â–¼';
}

.xr-section-summary-in:checked + label > span {
  display: none;
}

.xr-section-summary,
.xr-section-inline-details {
  padding-top: 4px;
  padding-bottom: 4px;
}

.xr-section-inline-details {
  grid-column: 2 / -1;
}

.xr-section-details {
  display: none;
  grid-column: 1 / -1;
  margin-bottom: 5px;
}

.xr-section-summary-in:checked ~ .xr-section-details {
  display: contents;
}

.xr-array-wrap {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 20px auto;
}

.xr-array-wrap > label {
  grid-column: 1;
  vertical-align: top;
}

.xr-preview {
  color: var(--xr-font-color3);
}

.xr-array-preview,
.xr-array-data {
  padding: 0 5px !important;
  grid-column: 2;
}

.xr-array-data,
.xr-array-in:checked ~ .xr-array-preview {
  display: none;
}

.xr-array-in:checked ~ .xr-array-data,
.xr-array-preview {
  display: inline-block;
}

.xr-dim-list {
  display: inline-block !important;
  list-style: none;
  padding: 0 !important;
  margin: 0;
}

.xr-dim-list li {
  display: inline-block;
  padding: 0;
  margin: 0;
}

.xr-dim-list:before {
  content: '(';
}

.xr-dim-list:after {
  content: ')';
}

.xr-dim-list li:not(:last-child):after {
  content: ',';
  padding-right: 5px;
}

.xr-has-index {
  font-weight: bold;
}

.xr-var-list,
.xr-var-item {
  display: contents;
}

.xr-var-item > div,
.xr-var-item label,
.xr-var-item > .xr-var-name span {
  background-color: var(--xr-background-color-row-even);
  margin-bottom: 0;
}

.xr-var-item > .xr-var-name:hover span {
  padding-right: 5px;
}

.xr-var-list > li:nth-child(odd) > div,
.xr-var-list > li:nth-child(odd) > label,
.xr-var-list > li:nth-child(odd) > .xr-var-name span {
  background-color: var(--xr-background-color-row-odd);
}

.xr-var-name {
  grid-column: 1;
}

.xr-var-dims {
  grid-column: 2;
}

.xr-var-dtype {
  grid-column: 3;
  text-align: right;
  color: var(--xr-font-color2);
}

.xr-var-preview {
  grid-column: 4;
}

.xr-var-name,
.xr-var-dims,
.xr-var-dtype,
.xr-preview,
.xr-attrs dt {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 10px;
}

.xr-var-name:hover,
.xr-var-dims:hover,
.xr-var-dtype:hover,
.xr-attrs dt:hover {
  overflow: visible;
  width: auto;
  z-index: 1;
}

.xr-var-attrs,
.xr-var-data {
  display: none;
  background-color: var(--xr-background-color) !important;
  padding-bottom: 5px !important;
}

.xr-var-attrs-in:checked ~ .xr-var-attrs,
.xr-var-data-in:checked ~ .xr-var-data {
  display: block;
}

.xr-var-data > table {
  float: right;
}

.xr-var-name span,
.xr-var-data,
.xr-attrs {
  padding-left: 25px !important;
}

.xr-attrs,
.xr-var-attrs,
.xr-var-data {
  grid-column: 1 / -1;
}

dl.xr-attrs {
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 125px auto;
}

.xr-attrs dt,
.xr-attrs dd {
  padding: 0;
  margin: 0;
  float: left;
  padding-right: 10px;
  width: auto;
}

.xr-attrs dt {
  font-weight: normal;
  grid-column: 1;
}

.xr-attrs dt:hover span {
  display: inline-block;
  background: var(--xr-background-color);
  padding-right: 10px;
}

.xr-attrs dd {
  grid-column: 2;
  white-space: pre-wrap;
  word-break: break-all;
}

.xr-icon-database,
.xr-icon-file-text2 {
  display: inline-block;
  vertical-align: middle;
  width: 1em;
  height: 1.5em !important;
  stroke-width: 0;
  stroke: currentColor;
  fill: currentColor;
}
</style><pre class='xr-text-repr-fallback'>&lt;xarray.DataArray &#x27;stacked_eumetsat_data&#x27; (variable: 12, y: 1831, x: 1870)&gt;
dask.array&lt;concatenate, shape=(12, 1831, 1870), dtype=float32, chunksize=(1, 1831, 1870), chunktype=numpy.ndarray&gt;
Coordinates:
  * y         (y) float64 9.012e+06 9.008e+06 9.004e+06 ... 1.696e+06 1.692e+06
  * x         (x) float64 -3.088e+06 -3.084e+06 ... 4.384e+06 4.388e+06
  * variable  (variable) object &#x27;HRV&#x27; &#x27;IR_016&#x27; &#x27;IR_039&#x27; ... &#x27;WV_062&#x27; &#x27;WV_073&#x27;
Attributes:
    orbital_parameters:                     {&#x27;projection_longitude&#x27;: 9.5, &#x27;pr...
    sun_earth_distance_correction_applied:  True
    sun_earth_distance_correction_factor:   0.9911189780118609
    units:                                  %
    wavelength:                             0.7â€¯ÂµmÂ (0.5-0.9â€¯Âµm)
    standard_name:                          toa_bidirectional_reflectance
    platform_name:                          Meteosat-10
    sensor:                                 seviri
    start_time:                             2021-03-19 13:15:09.278906
    end_time:                               2021-03-19 13:20:10.330158
    area:                                   Area ID: geos_seviri_hrv\nDescrip...
    name:                                   HRV
    resolution:                             1000.134348869
    calibration:                            reflectance
    modifiers:                              ()
    _satpy_id:                              DataID(name=&#x27;HRV&#x27;, wavelength=Wav...
    ancillary_variables:                    []</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.DataArray</div><div class='xr-array-name'>'stacked_eumetsat_data'</div><ul class='xr-dim-list'><li><span class='xr-has-index'>variable</span>: 12</li><li><span class='xr-has-index'>y</span>: 1831</li><li><span class='xr-has-index'>x</span>: 1870</li></ul></div><ul class='xr-sections'><li class='xr-section-item'><div class='xr-array-wrap'><input id='section-3df9f2ff-85ef-4246-859b-aafd2fbc6d16' class='xr-array-in' type='checkbox' checked><label for='section-3df9f2ff-85ef-4246-859b-aafd2fbc6d16' title='Show/hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-array-preview xr-preview'><span>dask.array&lt;chunksize=(1, 1831, 1870), meta=np.ndarray&gt;</span></div><div class='xr-array-data'><table>
<tr>
<td>
<table>
  <thead>
    <tr><td> </td><th> Array </th><th> Chunk </th></tr>
  </thead>
  <tbody>
    <tr><th> Bytes </th><td> 164.35 MB </td> <td> 13.70 MB </td></tr>
    <tr><th> Shape </th><td> (12, 1831, 1870) </td> <td> (1, 1831, 1870) </td></tr>
    <tr><th> Count </th><td> 1335 Tasks </td><td> 12 Chunks </td></tr>
    <tr><th> Type </th><td> float32 </td><td> numpy.ndarray </td></tr>
  </tbody>
</table>
</td>
<td>
<svg width="194" height="182" style="stroke:rgb(0,0,0);stroke-width:1" >

  <!-- Horizontal lines -->
  <line x1="10" y1="0" x2="24" y2="14" style="stroke-width:2" />
  <line x1="10" y1="117" x2="24" y2="132" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="10" y1="0" x2="10" y2="117" style="stroke-width:2" />
  <line x1="11" y1="1" x2="11" y2="118" />
  <line x1="12" y1="2" x2="12" y2="119" />
  <line x1="13" y1="3" x2="13" y2="121" />
  <line x1="14" y1="4" x2="14" y2="122" />
  <line x1="16" y1="6" x2="16" y2="123" />
  <line x1="17" y1="7" x2="17" y2="124" />
  <line x1="18" y1="8" x2="18" y2="126" />
  <line x1="19" y1="9" x2="19" y2="127" />
  <line x1="21" y1="11" x2="21" y2="128" />
  <line x1="22" y1="12" x2="22" y2="129" />
  <line x1="23" y1="13" x2="23" y2="131" />
  <line x1="24" y1="14" x2="24" y2="132" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="10.0,0.0 24.9485979497544,14.948597949754403 24.9485979497544,132.44592415296296 10.0,117.49732620320856" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="10" y1="0" x2="130" y2="0" style="stroke-width:2" />
  <line x1="11" y1="1" x2="131" y2="1" />
  <line x1="12" y1="2" x2="132" y2="2" />
  <line x1="13" y1="3" x2="133" y2="3" />
  <line x1="14" y1="4" x2="134" y2="4" />
  <line x1="16" y1="6" x2="136" y2="6" />
  <line x1="17" y1="7" x2="137" y2="7" />
  <line x1="18" y1="8" x2="138" y2="8" />
  <line x1="19" y1="9" x2="139" y2="9" />
  <line x1="21" y1="11" x2="141" y2="11" />
  <line x1="22" y1="12" x2="142" y2="12" />
  <line x1="23" y1="13" x2="143" y2="13" />
  <line x1="24" y1="14" x2="144" y2="14" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="10" y1="0" x2="24" y2="14" style="stroke-width:2" />
  <line x1="130" y1="0" x2="144" y2="14" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="10.0,0.0 130.0,0.0 144.9485979497544,14.948597949754403 24.9485979497544,14.948597949754403" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="24" y1="14" x2="144" y2="14" style="stroke-width:2" />
  <line x1="24" y1="132" x2="144" y2="132" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="24" y1="14" x2="24" y2="132" style="stroke-width:2" />
  <line x1="144" y1="14" x2="144" y2="132" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="24.9485979497544,14.948597949754403 144.9485979497544,14.948597949754403 144.9485979497544,132.44592415296296 24.9485979497544,132.44592415296296" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Text -->
  <text x="84.948598" y="152.445924" font-size="1.0rem" font-weight="100" text-anchor="middle" >1870</text>
  <text x="164.948598" y="73.697261" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(-90,164.948598,73.697261)">1831</text>
  <text x="7.474299" y="144.971625" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(45,7.474299,144.971625)">12</text>
</svg>
</td>
</tr>
</table></div></div></li><li class='xr-section-item'><input id='section-d1b355e6-0474-4e22-b2d5-204f8e74f124' class='xr-section-summary-in' type='checkbox'  checked><label for='section-d1b355e6-0474-4e22-b2d5-204f8e74f124' class='xr-section-summary' >Coordinates: <span>(3)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>9.012e+06 9.008e+06 ... 1.692e+06</div><input id='attrs-15760121-21cc-4783-8c64-5b87a7b6a81a' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-15760121-21cc-4783-8c64-5b87a7b6a81a' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-5fa89cd5-46c2-4631-a2c0-bc52e0d511cf' class='xr-var-data-in' type='checkbox'><label for='data-5fa89cd5-46c2-4631-a2c0-bc52e0d511cf' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([9012000., 9008000., 9004000., ..., 1700000., 1696000., 1692000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>-3.088e+06 -3.084e+06 ... 4.388e+06</div><input id='attrs-5298ee29-2ee1-40fc-8db6-cdf108376caf' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-5298ee29-2ee1-40fc-8db6-cdf108376caf' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-47d5e03c-34a6-40b6-840c-c5f3a895be33' class='xr-var-data-in' type='checkbox'><label for='data-47d5e03c-34a6-40b6-840c-c5f3a895be33' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([-3088000., -3084000., -3080000., ...,  4380000.,  4384000.,  4388000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>variable</span></div><div class='xr-var-dims'>(variable)</div><div class='xr-var-dtype'>object</div><div class='xr-var-preview xr-preview'>&#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;</div><input id='attrs-3df88dae-8221-4559-b8b6-1d25e67e5c92' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-3df88dae-8221-4559-b8b6-1d25e67e5c92' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-4a0dad21-2c1a-43c4-b4ec-e2e7804bc5d5' class='xr-var-data-in' type='checkbox'><label for='data-4a0dad21-2c1a-43c4-b4ec-e2e7804bc5d5' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;HRV&#x27;, &#x27;IR_016&#x27;, &#x27;IR_039&#x27;, &#x27;IR_087&#x27;, &#x27;IR_097&#x27;, &#x27;IR_108&#x27;, &#x27;IR_120&#x27;,
       &#x27;IR_134&#x27;, &#x27;VIS006&#x27;, &#x27;VIS008&#x27;, &#x27;WV_062&#x27;, &#x27;WV_073&#x27;], dtype=object)</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-e65ae250-3998-4049-8874-484ec6845b14' class='xr-section-summary-in' type='checkbox'  ><label for='section-e65ae250-3998-4049-8874-484ec6845b14' class='xr-section-summary' >Attributes: <span>(17)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'><dt><span>orbital_parameters :</span></dt><dd>{&#x27;projection_longitude&#x27;: 9.5, &#x27;projection_latitude&#x27;: 0.0, &#x27;projection_altitude&#x27;: 35785831.0}</dd><dt><span>sun_earth_distance_correction_applied :</span></dt><dd>True</dd><dt><span>sun_earth_distance_correction_factor :</span></dt><dd>0.9911189780118609</dd><dt><span>units :</span></dt><dd>%</dd><dt><span>wavelength :</span></dt><dd>0.7â€¯ÂµmÂ (0.5-0.9â€¯Âµm)</dd><dt><span>standard_name :</span></dt><dd>toa_bidirectional_reflectance</dd><dt><span>platform_name :</span></dt><dd>Meteosat-10</dd><dt><span>sensor :</span></dt><dd>seviri</dd><dt><span>start_time :</span></dt><dd>2021-03-19 13:15:09.278906</dd><dt><span>end_time :</span></dt><dd>2021-03-19 13:20:10.330158</dd><dt><span>area :</span></dt><dd>Area ID: geos_seviri_hrv
Description: SEVIRI high resolution channel area
Projection ID: seviri_hrv
Projection: {&#x27;a&#x27;: &#x27;6378169&#x27;, &#x27;h&#x27;: &#x27;35785831&#x27;, &#x27;lon_0&#x27;: &#x27;9.5&#x27;, &#x27;no_defs&#x27;: &#x27;None&#x27;, &#x27;proj&#x27;: &#x27;geos&#x27;, &#x27;rf&#x27;: &#x27;295.488065897014&#x27;, &#x27;type&#x27;: &#x27;crs&#x27;, &#x27;units&#x27;: &#x27;m&#x27;, &#x27;x_0&#x27;: &#x27;0&#x27;, &#x27;y_0&#x27;: &#x27;0&#x27;}
Number of columns: 5568
Number of rows: 4176
Area extent: (2790874.9005, 5571248.3904, -2777873.154, 1394687.3495)</dd><dt><span>name :</span></dt><dd>HRV</dd><dt><span>resolution :</span></dt><dd>1000.134348869</dd><dt><span>calibration :</span></dt><dd>reflectance</dd><dt><span>modifiers :</span></dt><dd>()</dd><dt><span>_satpy_id :</span></dt><dd>DataID(name=&#x27;HRV&#x27;, wavelength=WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), resolution=1000.134348869, calibration=&lt;calibration.reflectance&gt;, modifiers=())</dd><dt><span>ancillary_variables :</span></dt><dd>[]</dd></dl></div></li></ul></div></div>



<br>

### Compressing

We'll now develop our compressor class that will reduce the size of the datasets that we save to Zarr, in this instance we'll normalize the data and transform it to Int16. This has been found to reduce the size by ~50%.

```python
#exports
def add_constant_coord_to_da(da, coord_name, coord_val):
    """
    Adds a new coordinate with a 
    constant value to the DataArray
    
    Parameters
    ----------
    da : xr.DataArray
        DataArrray which will have the new coords added to it
    coord_name : str
        Name for the new coordinate dimensions
    coord_val
        Value that will be assigned to the new coordinates
        
    Returns
    -------
    da : xr.DataArray
        DataArrray with the new coords added to it
    
    """
    
    da = (da
          .assign_coords({coord_name:coord_val})
          .expand_dims(coord_name)
         )
    
    return da

class Compressor:
    def __init__(self, 
                 bits_per_pixel=10, 
                 mins=np.array([-1.2278595, -2.5118103, -64.83977, 63.404694, 2.844452, 199.10002, -17.254883, -26.29155, -1.1009827, -2.4184198, 199.57048, 198.95093]), 
                 maxs=np.array([103.90016, 69.60857, 339.15588, 340.26526, 317.86752, 313.2767, 315.99194, 274.82297, 93.786545, 101.34922, 249.91806, 286.96323]),
                 variable_order=['HRV', 'IR_016', 'IR_039', 'IR_087', 'IR_097', 'IR_108', 'IR_120', 'IR_134', 'VIS006', 'VIS008', 'WV_062', 'WV_073']
                ):
        
        locals_ = locals()
        attrs_to_add = ['bits_per_pixel', 'mins', 'maxs', 'variable_order']
        
        for attr in attrs_to_add:
            setattr(self, attr, locals_[attr])
            
        return
    
    def fit(self, da, dims=['time', 'y', 'x']):
        self.mins = da.min(dims).compute()
        self.maxs = da.max(dims).compute()
        self.variable_order = da.coords['variable'].values
        
        print(f'The mins are: {self.mins}')
        print(f'The maxs are: {self.maxs}')
        print(f'The variable order is: {self.variable_order}')
        
        return

    def compress(self, da):
        da_meta = da.attrs 
        
        for attr in ['mins', 'maxs']:
            assert getattr(self, attr) is not None, f'{attr} must be set in initialisation or through `fit`'

        if 'time' not in da.dims:
            time = pd.to_datetime(da_meta['end_time'])
            da = add_constant_coord_to_da(da, 'time', time)

        da = (da
              .reindex({'variable': self.variable_order})
              .transpose('time', 'y', 'x', 'variable')
             )

        upper_bound = (2 ** self.bits_per_pixel) - 1
        new_max = self.maxs - self.mins

        da -= self.mins
        da /= new_max
        da *= upper_bound

        da = (da
              .clip(0, upper_bound)
              .fillna(-1)
              .round()
              .astype(np.int16)
             )

        da.attrs = {'meta': str(da_meta)} # Must be serialisable

        return da
```

```python
%%time

compressor = Compressor()

da_compressed = compressor.compress(ds_reproj['stacked_eumetsat_data'])
```

    CPU times: user 10.7 ms, sys: 1.96 ms, total: 12.7 ms
    Wall time: 12.6 ms
    

<br>

### Saving to Zarr

We'll now create a helper function for saving the data-array to a zarr database

```python
# exports
get_time_as_unix = lambda da: pd.Series((pd.to_datetime(da.time.values) - pd.Timestamp('1970-01-01')).total_seconds()).astype(int).values

def save_da_to_zarr(da, zarr_bucket, dim_order=['time', 'x', 'y', 'variable'], zarr_mode='a'):
    da = da.transpose(*dim_order)
    da['time'] = get_time_as_unix(da)
    
    _, y_size, x_size, _ = da.shape
    out_store = gcsfs.GCSMap(root=zarr_bucket, gcs=gcsfs.GCSFileSystem())

    chunks = (36, y_size, x_size, 1)

    ds = xr.Dataset({'stacked_eumetsat_data': da.chunk(chunks)})
    
    zarr_mode_to_extra_kwargs = {
        'a': {
            'append_dim': 'time'
        },
        'w': {
            'encoding': {
                'stacked_eumetsat_data': {
                    'compressor': numcodecs.Blosc(cname='zstd', clevel=5),
                    'chunks': chunks
                }
            }
        }
    }
    
    assert zarr_mode in ['a', 'w'], '`zarr_mode` must be one of: `a`, `w`'
    extra_kwargs = zarr_mode_to_extra_kwargs[zarr_mode]
    
    ds.to_zarr(out_store, mode=zarr_mode, consolidated=True, **extra_kwargs)
    print('Saved file to zarr bucket')
    return ds
```

```python
da_compressed
```




<div><svg style="position: absolute; width: 0; height: 0; overflow: hidden">
<defs>
<symbol id="icon-database" viewBox="0 0 32 32">
<path d="M16 0c-8.837 0-16 2.239-16 5v4c0 2.761 7.163 5 16 5s16-2.239 16-5v-4c0-2.761-7.163-5-16-5z"></path>
<path d="M16 17c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
<path d="M16 26c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
</symbol>
<symbol id="icon-file-text2" viewBox="0 0 32 32">
<path d="M28.681 7.159c-0.694-0.947-1.662-2.053-2.724-3.116s-2.169-2.030-3.116-2.724c-1.612-1.182-2.393-1.319-2.841-1.319h-15.5c-1.378 0-2.5 1.121-2.5 2.5v27c0 1.378 1.122 2.5 2.5 2.5h23c1.378 0 2.5-1.122 2.5-2.5v-19.5c0-0.448-0.137-1.23-1.319-2.841zM24.543 5.457c0.959 0.959 1.712 1.825 2.268 2.543h-4.811v-4.811c0.718 0.556 1.584 1.309 2.543 2.268zM28 29.5c0 0.271-0.229 0.5-0.5 0.5h-23c-0.271 0-0.5-0.229-0.5-0.5v-27c0-0.271 0.229-0.5 0.5-0.5 0 0 15.499-0 15.5 0v7c0 0.552 0.448 1 1 1h7v19.5z"></path>
<path d="M23 26h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
<path d="M23 22h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
<path d="M23 18h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
</symbol>
</defs>
</svg>
<style>/* CSS stylesheet for displaying xarray objects in jupyterlab.
 *
 */

:root {
  --xr-font-color0: var(--jp-content-font-color0, rgba(0, 0, 0, 1));
  --xr-font-color2: var(--jp-content-font-color2, rgba(0, 0, 0, 0.54));
  --xr-font-color3: var(--jp-content-font-color3, rgba(0, 0, 0, 0.38));
  --xr-border-color: var(--jp-border-color2, #e0e0e0);
  --xr-disabled-color: var(--jp-layout-color3, #bdbdbd);
  --xr-background-color: var(--jp-layout-color0, white);
  --xr-background-color-row-even: var(--jp-layout-color1, white);
  --xr-background-color-row-odd: var(--jp-layout-color2, #eeeeee);
}

html[theme=dark],
body.vscode-dark {
  --xr-font-color0: rgba(255, 255, 255, 1);
  --xr-font-color2: rgba(255, 255, 255, 0.54);
  --xr-font-color3: rgba(255, 255, 255, 0.38);
  --xr-border-color: #1F1F1F;
  --xr-disabled-color: #515151;
  --xr-background-color: #111111;
  --xr-background-color-row-even: #111111;
  --xr-background-color-row-odd: #313131;
}

.xr-wrap {
  display: block;
  min-width: 300px;
  max-width: 700px;
}

.xr-text-repr-fallback {
  /* fallback to plain text repr when CSS is not injected (untrusted notebook) */
  display: none;
}

.xr-header {
  padding-top: 6px;
  padding-bottom: 6px;
  margin-bottom: 4px;
  border-bottom: solid 1px var(--xr-border-color);
}

.xr-header > div,
.xr-header > ul {
  display: inline;
  margin-top: 0;
  margin-bottom: 0;
}

.xr-obj-type,
.xr-array-name {
  margin-left: 2px;
  margin-right: 10px;
}

.xr-obj-type {
  color: var(--xr-font-color2);
}

.xr-sections {
  padding-left: 0 !important;
  display: grid;
  grid-template-columns: 150px auto auto 1fr 20px 20px;
}

.xr-section-item {
  display: contents;
}

.xr-section-item input {
  display: none;
}

.xr-section-item input + label {
  color: var(--xr-disabled-color);
}

.xr-section-item input:enabled + label {
  cursor: pointer;
  color: var(--xr-font-color2);
}

.xr-section-item input:enabled + label:hover {
  color: var(--xr-font-color0);
}

.xr-section-summary {
  grid-column: 1;
  color: var(--xr-font-color2);
  font-weight: 500;
}

.xr-section-summary > span {
  display: inline-block;
  padding-left: 0.5em;
}

.xr-section-summary-in:disabled + label {
  color: var(--xr-font-color2);
}

.xr-section-summary-in + label:before {
  display: inline-block;
  content: 'â–º';
  font-size: 11px;
  width: 15px;
  text-align: center;
}

.xr-section-summary-in:disabled + label:before {
  color: var(--xr-disabled-color);
}

.xr-section-summary-in:checked + label:before {
  content: 'â–¼';
}

.xr-section-summary-in:checked + label > span {
  display: none;
}

.xr-section-summary,
.xr-section-inline-details {
  padding-top: 4px;
  padding-bottom: 4px;
}

.xr-section-inline-details {
  grid-column: 2 / -1;
}

.xr-section-details {
  display: none;
  grid-column: 1 / -1;
  margin-bottom: 5px;
}

.xr-section-summary-in:checked ~ .xr-section-details {
  display: contents;
}

.xr-array-wrap {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 20px auto;
}

.xr-array-wrap > label {
  grid-column: 1;
  vertical-align: top;
}

.xr-preview {
  color: var(--xr-font-color3);
}

.xr-array-preview,
.xr-array-data {
  padding: 0 5px !important;
  grid-column: 2;
}

.xr-array-data,
.xr-array-in:checked ~ .xr-array-preview {
  display: none;
}

.xr-array-in:checked ~ .xr-array-data,
.xr-array-preview {
  display: inline-block;
}

.xr-dim-list {
  display: inline-block !important;
  list-style: none;
  padding: 0 !important;
  margin: 0;
}

.xr-dim-list li {
  display: inline-block;
  padding: 0;
  margin: 0;
}

.xr-dim-list:before {
  content: '(';
}

.xr-dim-list:after {
  content: ')';
}

.xr-dim-list li:not(:last-child):after {
  content: ',';
  padding-right: 5px;
}

.xr-has-index {
  font-weight: bold;
}

.xr-var-list,
.xr-var-item {
  display: contents;
}

.xr-var-item > div,
.xr-var-item label,
.xr-var-item > .xr-var-name span {
  background-color: var(--xr-background-color-row-even);
  margin-bottom: 0;
}

.xr-var-item > .xr-var-name:hover span {
  padding-right: 5px;
}

.xr-var-list > li:nth-child(odd) > div,
.xr-var-list > li:nth-child(odd) > label,
.xr-var-list > li:nth-child(odd) > .xr-var-name span {
  background-color: var(--xr-background-color-row-odd);
}

.xr-var-name {
  grid-column: 1;
}

.xr-var-dims {
  grid-column: 2;
}

.xr-var-dtype {
  grid-column: 3;
  text-align: right;
  color: var(--xr-font-color2);
}

.xr-var-preview {
  grid-column: 4;
}

.xr-var-name,
.xr-var-dims,
.xr-var-dtype,
.xr-preview,
.xr-attrs dt {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 10px;
}

.xr-var-name:hover,
.xr-var-dims:hover,
.xr-var-dtype:hover,
.xr-attrs dt:hover {
  overflow: visible;
  width: auto;
  z-index: 1;
}

.xr-var-attrs,
.xr-var-data {
  display: none;
  background-color: var(--xr-background-color) !important;
  padding-bottom: 5px !important;
}

.xr-var-attrs-in:checked ~ .xr-var-attrs,
.xr-var-data-in:checked ~ .xr-var-data {
  display: block;
}

.xr-var-data > table {
  float: right;
}

.xr-var-name span,
.xr-var-data,
.xr-attrs {
  padding-left: 25px !important;
}

.xr-attrs,
.xr-var-attrs,
.xr-var-data {
  grid-column: 1 / -1;
}

dl.xr-attrs {
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 125px auto;
}

.xr-attrs dt,
.xr-attrs dd {
  padding: 0;
  margin: 0;
  float: left;
  padding-right: 10px;
  width: auto;
}

.xr-attrs dt {
  font-weight: normal;
  grid-column: 1;
}

.xr-attrs dt:hover span {
  display: inline-block;
  background: var(--xr-background-color);
  padding-right: 10px;
}

.xr-attrs dd {
  grid-column: 2;
  white-space: pre-wrap;
  word-break: break-all;
}

.xr-icon-database,
.xr-icon-file-text2 {
  display: inline-block;
  vertical-align: middle;
  width: 1em;
  height: 1.5em !important;
  stroke-width: 0;
  stroke: currentColor;
  fill: currentColor;
}
</style><pre class='xr-text-repr-fallback'>&lt;xarray.DataArray &#x27;stacked_eumetsat_data&#x27; (time: 1, y: 1831, x: 1870, variable: 12)&gt;
dask.array&lt;astype, shape=(1, 1831, 1870, 12), dtype=int16, chunksize=(1, 1831, 1870, 1), chunktype=numpy.ndarray&gt;
Coordinates:
  * variable  (variable) object &#x27;HRV&#x27; &#x27;IR_016&#x27; &#x27;IR_039&#x27; ... &#x27;WV_062&#x27; &#x27;WV_073&#x27;
  * y         (y) float64 9.012e+06 9.008e+06 9.004e+06 ... 1.696e+06 1.692e+06
  * x         (x) float64 -3.088e+06 -3.084e+06 ... 4.384e+06 4.388e+06
  * time      (time) datetime64[ns] 2021-03-19T13:20:10.330158
Attributes:
    meta:     {&#x27;orbital_parameters&#x27;: {&#x27;projection_longitude&#x27;: 9.5, &#x27;projectio...</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.DataArray</div><div class='xr-array-name'>'stacked_eumetsat_data'</div><ul class='xr-dim-list'><li><span class='xr-has-index'>time</span>: 1</li><li><span class='xr-has-index'>y</span>: 1831</li><li><span class='xr-has-index'>x</span>: 1870</li><li><span class='xr-has-index'>variable</span>: 12</li></ul></div><ul class='xr-sections'><li class='xr-section-item'><div class='xr-array-wrap'><input id='section-fcaec95c-4579-42a5-8082-5af90766ace4' class='xr-array-in' type='checkbox' checked><label for='section-fcaec95c-4579-42a5-8082-5af90766ace4' title='Show/hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-array-preview xr-preview'><span>dask.array&lt;chunksize=(1, 1831, 1870, 1), meta=np.ndarray&gt;</span></div><div class='xr-array-data'><table>
<tr>
<td>
<table>
  <thead>
    <tr><td> </td><th> Array </th><th> Chunk </th></tr>
  </thead>
  <tbody>
    <tr><th> Bytes </th><td> 82.18 MB </td> <td> 6.85 MB </td></tr>
    <tr><th> Shape </th><td> (1, 1831, 1870, 12) </td> <td> (1, 1831, 1870, 1) </td></tr>
    <tr><th> Count </th><td> 1505 Tasks </td><td> 12 Chunks </td></tr>
    <tr><th> Type </th><td> int16 </td><td> numpy.ndarray </td></tr>
  </tbody>
</table>
</td>
<td>
<svg width="334" height="239" style="stroke:rgb(0,0,0);stroke-width:1" >

  <!-- Horizontal lines -->
  <line x1="0" y1="0" x2="25" y2="0" style="stroke-width:2" />
  <line x1="0" y1="25" x2="25" y2="25" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="0" y1="0" x2="0" y2="25" style="stroke-width:2" />
  <line x1="25" y1="0" x2="25" y2="25" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="0.0,0.0 25.412616514582485,0.0 25.412616514582485,25.412616514582485 0.0,25.412616514582485" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Text -->
  <text x="12.706308" y="45.412617" font-size="1.0rem" font-weight="100" text-anchor="middle" >1</text>
  <text x="45.412617" y="12.706308" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(0,45.412617,12.706308)">1</text>


  <!-- Horizontal lines -->
  <line x1="95" y1="0" x2="164" y2="69" style="stroke-width:2" />
  <line x1="95" y1="120" x2="164" y2="189" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="95" y1="0" x2="95" y2="120" style="stroke-width:2" />
  <line x1="164" y1="69" x2="164" y2="189" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="95.0,0.0 164.11607423718152,69.11607423718151 164.11607423718152,189.11607423718152 95.0,120.0" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="95" y1="0" x2="120" y2="0" style="stroke-width:2" />
  <line x1="164" y1="69" x2="189" y2="69" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="95" y1="0" x2="164" y2="69" style="stroke-width:2" />
  <line x1="97" y1="0" x2="166" y2="69" />
  <line x1="99" y1="0" x2="168" y2="69" />
  <line x1="101" y1="0" x2="170" y2="69" />
  <line x1="103" y1="0" x2="172" y2="69" />
  <line x1="105" y1="0" x2="174" y2="69" />
  <line x1="107" y1="0" x2="176" y2="69" />
  <line x1="109" y1="0" x2="178" y2="69" />
  <line x1="111" y1="0" x2="181" y2="69" />
  <line x1="114" y1="0" x2="183" y2="69" />
  <line x1="116" y1="0" x2="185" y2="69" />
  <line x1="118" y1="0" x2="187" y2="69" />
  <line x1="120" y1="0" x2="189" y2="69" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="95.0,0.0 120.41261651458248,0.0 189.52869075176397,69.11607423718151 164.11607423718152,69.11607423718151" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="164" y1="69" x2="189" y2="69" style="stroke-width:2" />
  <line x1="164" y1="189" x2="189" y2="189" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="164" y1="69" x2="164" y2="189" style="stroke-width:2" />
  <line x1="166" y1="69" x2="166" y2="189" />
  <line x1="168" y1="69" x2="168" y2="189" />
  <line x1="170" y1="69" x2="170" y2="189" />
  <line x1="172" y1="69" x2="172" y2="189" />
  <line x1="174" y1="69" x2="174" y2="189" />
  <line x1="176" y1="69" x2="176" y2="189" />
  <line x1="178" y1="69" x2="178" y2="189" />
  <line x1="181" y1="69" x2="181" y2="189" />
  <line x1="183" y1="69" x2="183" y2="189" />
  <line x1="185" y1="69" x2="185" y2="189" />
  <line x1="187" y1="69" x2="187" y2="189" />
  <line x1="189" y1="69" x2="189" y2="189" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="164.11607423718152,69.11607423718151 189.528690751764,69.11607423718151 189.528690751764,189.11607423718152 164.11607423718152,189.11607423718152" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Text -->
  <text x="176.822382" y="209.116074" font-size="1.0rem" font-weight="100" text-anchor="middle" >12</text>
  <text x="209.528691" y="129.116074" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(-90,209.528691,129.116074)">1870</text>
  <text x="119.558037" y="174.558037" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(45,119.558037,174.558037)">1831</text>
</svg>
</td>
</tr>
</table></div></div></li><li class='xr-section-item'><input id='section-92f78b9b-4b46-4bec-a429-a1d37dce9c00' class='xr-section-summary-in' type='checkbox'  checked><label for='section-92f78b9b-4b46-4bec-a429-a1d37dce9c00' class='xr-section-summary' >Coordinates: <span>(4)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>variable</span></div><div class='xr-var-dims'>(variable)</div><div class='xr-var-dtype'>object</div><div class='xr-var-preview xr-preview'>&#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;</div><input id='attrs-9ca9cdff-df2d-4de7-b7ce-0e60c97a1357' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-9ca9cdff-df2d-4de7-b7ce-0e60c97a1357' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-bd9c3f46-5bac-4980-9afd-0968dc06d9ed' class='xr-var-data-in' type='checkbox'><label for='data-bd9c3f46-5bac-4980-9afd-0968dc06d9ed' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;HRV&#x27;, &#x27;IR_016&#x27;, &#x27;IR_039&#x27;, &#x27;IR_087&#x27;, &#x27;IR_097&#x27;, &#x27;IR_108&#x27;, &#x27;IR_120&#x27;,
       &#x27;IR_134&#x27;, &#x27;VIS006&#x27;, &#x27;VIS008&#x27;, &#x27;WV_062&#x27;, &#x27;WV_073&#x27;], dtype=object)</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>9.012e+06 9.008e+06 ... 1.692e+06</div><input id='attrs-642378dd-9ed5-4b15-824f-1649fa0580e0' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-642378dd-9ed5-4b15-824f-1649fa0580e0' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-b3cce48a-7a98-4999-b71b-e5318d48185c' class='xr-var-data-in' type='checkbox'><label for='data-b3cce48a-7a98-4999-b71b-e5318d48185c' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([9012000., 9008000., 9004000., ..., 1700000., 1696000., 1692000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>-3.088e+06 -3.084e+06 ... 4.388e+06</div><input id='attrs-790df2a8-aa33-49db-8fb5-33b3427dc208' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-790df2a8-aa33-49db-8fb5-33b3427dc208' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-552a10b1-2b7b-4bd7-a124-4a3c53224fd3' class='xr-var-data-in' type='checkbox'><label for='data-552a10b1-2b7b-4bd7-a124-4a3c53224fd3' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([-3088000., -3084000., -3080000., ...,  4380000.,  4384000.,  4388000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>time</span></div><div class='xr-var-dims'>(time)</div><div class='xr-var-dtype'>datetime64[ns]</div><div class='xr-var-preview xr-preview'>2021-03-19T13:20:10.330158</div><input id='attrs-b7dba93f-7518-49f6-b737-36898faf55e6' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-b7dba93f-7518-49f6-b737-36898faf55e6' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-c2f06ad8-306a-47df-8cd5-28200a6250b1' class='xr-var-data-in' type='checkbox'><label for='data-c2f06ad8-306a-47df-8cd5-28200a6250b1' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;2021-03-19T13:20:10.330158000&#x27;], dtype=&#x27;datetime64[ns]&#x27;)</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-a0c666ed-6244-4f91-b7c2-6cb8ffc6dee2' class='xr-section-summary-in' type='checkbox'  checked><label for='section-a0c666ed-6244-4f91-b7c2-6cb8ffc6dee2' class='xr-section-summary' >Attributes: <span>(1)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'><dt><span>meta :</span></dt><dd>{&#x27;orbital_parameters&#x27;: {&#x27;projection_longitude&#x27;: 9.5, &#x27;projection_latitude&#x27;: 0.0, &#x27;projection_altitude&#x27;: 35785831.0}, &#x27;sun_earth_distance_correction_applied&#x27;: True, &#x27;sun_earth_distance_correction_factor&#x27;: 0.9911189780118609, &#x27;units&#x27;: &#x27;%&#x27;, &#x27;wavelength&#x27;: WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), &#x27;standard_name&#x27;: &#x27;toa_bidirectional_reflectance&#x27;, &#x27;platform_name&#x27;: &#x27;Meteosat-10&#x27;, &#x27;sensor&#x27;: &#x27;seviri&#x27;, &#x27;start_time&#x27;: datetime.datetime(2021, 3, 19, 13, 15, 9, 278906), &#x27;end_time&#x27;: datetime.datetime(2021, 3, 19, 13, 20, 10, 330158), &#x27;area&#x27;: Area ID: geos_seviri_hrv
Description: SEVIRI high resolution channel area
Projection ID: seviri_hrv
Projection: {&#x27;a&#x27;: &#x27;6378169&#x27;, &#x27;h&#x27;: &#x27;35785831&#x27;, &#x27;lon_0&#x27;: &#x27;9.5&#x27;, &#x27;no_defs&#x27;: &#x27;None&#x27;, &#x27;proj&#x27;: &#x27;geos&#x27;, &#x27;rf&#x27;: &#x27;295.488065897014&#x27;, &#x27;type&#x27;: &#x27;crs&#x27;, &#x27;units&#x27;: &#x27;m&#x27;, &#x27;x_0&#x27;: &#x27;0&#x27;, &#x27;y_0&#x27;: &#x27;0&#x27;}
Number of columns: 5568
Number of rows: 4176
Area extent: (2790874.9005, 5571248.3904, -2777873.154, 1394687.3495), &#x27;name&#x27;: &#x27;HRV&#x27;, &#x27;resolution&#x27;: 1000.134348869, &#x27;calibration&#x27;: &#x27;reflectance&#x27;, &#x27;modifiers&#x27;: (), &#x27;_satpy_id&#x27;: DataID(name=&#x27;HRV&#x27;, wavelength=WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), resolution=1000.134348869, calibration=&lt;calibration.reflectance&gt;, modifiers=()), &#x27;ancillary_variables&#x27;: []}</dd></dl></div></li></ul></div></div>



<br>

Now we can save it!

```python
save_data = False

if save_data == True:
    out_zarr_bucket = 'solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/zarr_full_extent_TM_int16'
    ds = save_da_to_zarr(da_compressed, out_zarr_bucket, zarr_mode='w')
```

    /Users/laurence/conda/envs/satip_dev/lib/python3.8/site-packages/dask/core.py:121: RuntimeWarning: divide by zero encountered in true_divide
      return func(*(_execute_task(a, cache) for a in args))
    /Users/laurence/conda/envs/satip_dev/lib/python3.8/site-packages/dask/core.py:121: RuntimeWarning: invalid value encountered in sin
      return func(*(_execute_task(a, cache) for a in args))
    /Users/laurence/conda/envs/satip_dev/lib/python3.8/site-packages/dask/core.py:121: RuntimeWarning: invalid value encountered in cos
      return func(*(_execute_task(a, cache) for a in args))
    

    Saved file to zarr bucket
    

<br>

### Loading Zarr Data

We'll start by defining a loading function and a replacement for the standard `gcsfs.utils` `is_retriable` function

```python
#exports
def is_retriable(exception):
    """Returns True if this exception is retriable."""
    errors = list(range(500, 505)) + [
        400, # Jack's addition.  Google Cloud occasionally throws Bad Requests for no apparent reason.
        408,# Request Timeout
        429, # Too Many Requests
    ]
    
    errors += [str(e) for e in errors]
    
    if isinstance(exception, gcsfs.utils.HttpError):
        return exception.code in errors

    return isinstance(exception, gcsfs.utils.RETRIABLE_EXCEPTIONS)

gcsfs.utils.is_retriable = is_retriable

get_unix_as_time = lambda da: pd.to_datetime(da.time.values, unit='s')

def load_from_zarr_bucket(zarr_bucket):
    gcs = gcsfs.GCSFileSystem()
    store = gcsfs.GCSMap(root=zarr_bucket, gcs=gcs)
    ds = xr.open_zarr(store, consolidated=True)
    
    ds['time'] = get_unix_as_time(ds)
    
    return ds
```

<br>

We'll now read it in

```python
%%time

out_zarr_bucket = 'solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/zarr_full_extent_TM_int16'

ds_zarr = load_from_zarr_bucket(out_zarr_bucket)

ds_zarr.time.compute()
```

    CPU times: user 4.14 s, sys: 1.7 s, total: 5.84 s
    Wall time: 21.3 s
    




<div><svg style="position: absolute; width: 0; height: 0; overflow: hidden">
<defs>
<symbol id="icon-database" viewBox="0 0 32 32">
<path d="M16 0c-8.837 0-16 2.239-16 5v4c0 2.761 7.163 5 16 5s16-2.239 16-5v-4c0-2.761-7.163-5-16-5z"></path>
<path d="M16 17c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
<path d="M16 26c-8.837 0-16-2.239-16-5v6c0 2.761 7.163 5 16 5s16-2.239 16-5v-6c0 2.761-7.163 5-16 5z"></path>
</symbol>
<symbol id="icon-file-text2" viewBox="0 0 32 32">
<path d="M28.681 7.159c-0.694-0.947-1.662-2.053-2.724-3.116s-2.169-2.030-3.116-2.724c-1.612-1.182-2.393-1.319-2.841-1.319h-15.5c-1.378 0-2.5 1.121-2.5 2.5v27c0 1.378 1.122 2.5 2.5 2.5h23c1.378 0 2.5-1.122 2.5-2.5v-19.5c0-0.448-0.137-1.23-1.319-2.841zM24.543 5.457c0.959 0.959 1.712 1.825 2.268 2.543h-4.811v-4.811c0.718 0.556 1.584 1.309 2.543 2.268zM28 29.5c0 0.271-0.229 0.5-0.5 0.5h-23c-0.271 0-0.5-0.229-0.5-0.5v-27c0-0.271 0.229-0.5 0.5-0.5 0 0 15.499-0 15.5 0v7c0 0.552 0.448 1 1 1h7v19.5z"></path>
<path d="M23 26h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
<path d="M23 22h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
<path d="M23 18h-14c-0.552 0-1-0.448-1-1s0.448-1 1-1h14c0.552 0 1 0.448 1 1s-0.448 1-1 1z"></path>
</symbol>
</defs>
</svg>
<style>/* CSS stylesheet for displaying xarray objects in jupyterlab.
 *
 */

:root {
  --xr-font-color0: var(--jp-content-font-color0, rgba(0, 0, 0, 1));
  --xr-font-color2: var(--jp-content-font-color2, rgba(0, 0, 0, 0.54));
  --xr-font-color3: var(--jp-content-font-color3, rgba(0, 0, 0, 0.38));
  --xr-border-color: var(--jp-border-color2, #e0e0e0);
  --xr-disabled-color: var(--jp-layout-color3, #bdbdbd);
  --xr-background-color: var(--jp-layout-color0, white);
  --xr-background-color-row-even: var(--jp-layout-color1, white);
  --xr-background-color-row-odd: var(--jp-layout-color2, #eeeeee);
}

html[theme=dark],
body.vscode-dark {
  --xr-font-color0: rgba(255, 255, 255, 1);
  --xr-font-color2: rgba(255, 255, 255, 0.54);
  --xr-font-color3: rgba(255, 255, 255, 0.38);
  --xr-border-color: #1F1F1F;
  --xr-disabled-color: #515151;
  --xr-background-color: #111111;
  --xr-background-color-row-even: #111111;
  --xr-background-color-row-odd: #313131;
}

.xr-wrap {
  display: block;
  min-width: 300px;
  max-width: 700px;
}

.xr-text-repr-fallback {
  /* fallback to plain text repr when CSS is not injected (untrusted notebook) */
  display: none;
}

.xr-header {
  padding-top: 6px;
  padding-bottom: 6px;
  margin-bottom: 4px;
  border-bottom: solid 1px var(--xr-border-color);
}

.xr-header > div,
.xr-header > ul {
  display: inline;
  margin-top: 0;
  margin-bottom: 0;
}

.xr-obj-type,
.xr-array-name {
  margin-left: 2px;
  margin-right: 10px;
}

.xr-obj-type {
  color: var(--xr-font-color2);
}

.xr-sections {
  padding-left: 0 !important;
  display: grid;
  grid-template-columns: 150px auto auto 1fr 20px 20px;
}

.xr-section-item {
  display: contents;
}

.xr-section-item input {
  display: none;
}

.xr-section-item input + label {
  color: var(--xr-disabled-color);
}

.xr-section-item input:enabled + label {
  cursor: pointer;
  color: var(--xr-font-color2);
}

.xr-section-item input:enabled + label:hover {
  color: var(--xr-font-color0);
}

.xr-section-summary {
  grid-column: 1;
  color: var(--xr-font-color2);
  font-weight: 500;
}

.xr-section-summary > span {
  display: inline-block;
  padding-left: 0.5em;
}

.xr-section-summary-in:disabled + label {
  color: var(--xr-font-color2);
}

.xr-section-summary-in + label:before {
  display: inline-block;
  content: 'â–º';
  font-size: 11px;
  width: 15px;
  text-align: center;
}

.xr-section-summary-in:disabled + label:before {
  color: var(--xr-disabled-color);
}

.xr-section-summary-in:checked + label:before {
  content: 'â–¼';
}

.xr-section-summary-in:checked + label > span {
  display: none;
}

.xr-section-summary,
.xr-section-inline-details {
  padding-top: 4px;
  padding-bottom: 4px;
}

.xr-section-inline-details {
  grid-column: 2 / -1;
}

.xr-section-details {
  display: none;
  grid-column: 1 / -1;
  margin-bottom: 5px;
}

.xr-section-summary-in:checked ~ .xr-section-details {
  display: contents;
}

.xr-array-wrap {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 20px auto;
}

.xr-array-wrap > label {
  grid-column: 1;
  vertical-align: top;
}

.xr-preview {
  color: var(--xr-font-color3);
}

.xr-array-preview,
.xr-array-data {
  padding: 0 5px !important;
  grid-column: 2;
}

.xr-array-data,
.xr-array-in:checked ~ .xr-array-preview {
  display: none;
}

.xr-array-in:checked ~ .xr-array-data,
.xr-array-preview {
  display: inline-block;
}

.xr-dim-list {
  display: inline-block !important;
  list-style: none;
  padding: 0 !important;
  margin: 0;
}

.xr-dim-list li {
  display: inline-block;
  padding: 0;
  margin: 0;
}

.xr-dim-list:before {
  content: '(';
}

.xr-dim-list:after {
  content: ')';
}

.xr-dim-list li:not(:last-child):after {
  content: ',';
  padding-right: 5px;
}

.xr-has-index {
  font-weight: bold;
}

.xr-var-list,
.xr-var-item {
  display: contents;
}

.xr-var-item > div,
.xr-var-item label,
.xr-var-item > .xr-var-name span {
  background-color: var(--xr-background-color-row-even);
  margin-bottom: 0;
}

.xr-var-item > .xr-var-name:hover span {
  padding-right: 5px;
}

.xr-var-list > li:nth-child(odd) > div,
.xr-var-list > li:nth-child(odd) > label,
.xr-var-list > li:nth-child(odd) > .xr-var-name span {
  background-color: var(--xr-background-color-row-odd);
}

.xr-var-name {
  grid-column: 1;
}

.xr-var-dims {
  grid-column: 2;
}

.xr-var-dtype {
  grid-column: 3;
  text-align: right;
  color: var(--xr-font-color2);
}

.xr-var-preview {
  grid-column: 4;
}

.xr-var-name,
.xr-var-dims,
.xr-var-dtype,
.xr-preview,
.xr-attrs dt {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 10px;
}

.xr-var-name:hover,
.xr-var-dims:hover,
.xr-var-dtype:hover,
.xr-attrs dt:hover {
  overflow: visible;
  width: auto;
  z-index: 1;
}

.xr-var-attrs,
.xr-var-data {
  display: none;
  background-color: var(--xr-background-color) !important;
  padding-bottom: 5px !important;
}

.xr-var-attrs-in:checked ~ .xr-var-attrs,
.xr-var-data-in:checked ~ .xr-var-data {
  display: block;
}

.xr-var-data > table {
  float: right;
}

.xr-var-name span,
.xr-var-data,
.xr-attrs {
  padding-left: 25px !important;
}

.xr-attrs,
.xr-var-attrs,
.xr-var-data {
  grid-column: 1 / -1;
}

dl.xr-attrs {
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: 125px auto;
}

.xr-attrs dt,
.xr-attrs dd {
  padding: 0;
  margin: 0;
  float: left;
  padding-right: 10px;
  width: auto;
}

.xr-attrs dt {
  font-weight: normal;
  grid-column: 1;
}

.xr-attrs dt:hover span {
  display: inline-block;
  background: var(--xr-background-color);
  padding-right: 10px;
}

.xr-attrs dd {
  grid-column: 2;
  white-space: pre-wrap;
  word-break: break-all;
}

.xr-icon-database,
.xr-icon-file-text2 {
  display: inline-block;
  vertical-align: middle;
  width: 1em;
  height: 1.5em !important;
  stroke-width: 0;
  stroke: currentColor;
  fill: currentColor;
}
</style><pre class='xr-text-repr-fallback'>&lt;xarray.DataArray &#x27;time&#x27; (time: 5816)&gt;
array([&#x27;2021-03-19T13:20:10.000000000&#x27;, &#x27;2021-03-19T13:24:16.000000000&#x27;,
       &#x27;2021-03-19T13:29:17.000000000&#x27;, ..., &#x27;2020-03-14T23:49:18.000000000&#x27;,
       &#x27;2020-03-14T23:54:17.000000000&#x27;, &#x27;2020-03-14T23:59:15.000000000&#x27;],
      dtype=&#x27;datetime64[ns]&#x27;)
Coordinates:
  * time     (time) datetime64[ns] 2021-03-19T13:20:10 ... 2020-03-14T23:59:15</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.DataArray</div><div class='xr-array-name'>'time'</div><ul class='xr-dim-list'><li><span class='xr-has-index'>time</span>: 5816</li></ul></div><ul class='xr-sections'><li class='xr-section-item'><div class='xr-array-wrap'><input id='section-1f06b848-4cff-4ad8-92f7-6b93d8d0b477' class='xr-array-in' type='checkbox' checked><label for='section-1f06b848-4cff-4ad8-92f7-6b93d8d0b477' title='Show/hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-array-preview xr-preview'><span>2021-03-19T13:20:10 2021-03-19T13:24:16 ... 2020-03-14T23:59:15</span></div><div class='xr-array-data'><pre>array([&#x27;2021-03-19T13:20:10.000000000&#x27;, &#x27;2021-03-19T13:24:16.000000000&#x27;,
       &#x27;2021-03-19T13:29:17.000000000&#x27;, ..., &#x27;2020-03-14T23:49:18.000000000&#x27;,
       &#x27;2020-03-14T23:54:17.000000000&#x27;, &#x27;2020-03-14T23:59:15.000000000&#x27;],
      dtype=&#x27;datetime64[ns]&#x27;)</pre></div></div></li><li class='xr-section-item'><input id='section-18c7b3b9-ef8f-45da-8683-f146da27ba4d' class='xr-section-summary-in' type='checkbox'  checked><label for='section-18c7b3b9-ef8f-45da-8683-f146da27ba4d' class='xr-section-summary' >Coordinates: <span>(1)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>time</span></div><div class='xr-var-dims'>(time)</div><div class='xr-var-dtype'>datetime64[ns]</div><div class='xr-var-preview xr-preview'>2021-03-19T13:20:10 ... 2020-03-...</div><input id='attrs-93e4561d-e083-4a6e-9dda-d4a445c771a9' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-93e4561d-e083-4a6e-9dda-d4a445c771a9' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-bedb239d-e4d0-48bc-a042-22bfaa25911a' class='xr-var-data-in' type='checkbox'><label for='data-bedb239d-e4d0-48bc-a042-22bfaa25911a' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;2021-03-19T13:20:10.000000000&#x27;, &#x27;2021-03-19T13:24:16.000000000&#x27;,
       &#x27;2021-03-19T13:29:17.000000000&#x27;, ..., &#x27;2020-03-14T23:49:18.000000000&#x27;,
       &#x27;2020-03-14T23:54:17.000000000&#x27;, &#x27;2020-03-14T23:59:15.000000000&#x27;],
      dtype=&#x27;datetime64[ns]&#x27;)</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-1d5348a9-8c20-4476-8b24-22fde4674305' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-1d5348a9-8c20-4476-8b24-22fde4674305' class='xr-section-summary'  title='Expand/collapse section'>Attributes: <span>(0)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'></dl></div></li></ul></div></div>



<br>

Let's inspect the current datetime coverage in the database

```python
#exports
def plot_zarr_data(loaded_xarray):
    df = loaded_xarray.time.to_dataframe()
    df['time'] = 1
    df = df.resample('D').sum()

    # rather than messing with formatter, set index to a readable date format of Year-Month
    df = df.set_index(df.index.map(lambda s: s.strftime('%Y-%m')))

    # plot
    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
    sns.heatmap(df, ax=ax, cmap='Blues', xticklabels=False)

    ax.set(title="Count of timesteps by day in Zarr datastore")

    # reduce tick counts
    plt.locator_params(axis='y', nbins=10)
```

```python
plot_zarr_data(loaded_xarray)
```


![png](img/nbs/output_32_0.png)


<br>

We'll also plot the a sample of the loaded array

```python
fig = plt.figure(dpi=250, figsize=(10, 10))
ax = plt.axes(projection=ccrs.TransverseMercator())

loaded_xarray['stacked_eumetsat_data'].isel(variable=0, time=0).T.plot(ax=ax, cmap='magma', vmin=-200, vmax=400)

ax.coastlines(resolution='50m', alpha=0.8, color='white')
```

    <ipython-input-26-f7e189d5f897>:2: UserWarning: The default value for the *approx* keyword argument to TransverseMercator will change from True to False after 0.18.
      ax = plt.axes(projection=ccrs.TransverseMercator())
    




    <cartopy.mpl.feature_artist.FeatureArtist at 0x7fc2df31c0a0>




![png](img/nbs/output_34_2.png)


<br>

We can also identify missing datasets which will be useful for filling them in later

```python
#exports
def identifying_missing_datasets(start_date, end_date, eumetsat_zarr_bucket='solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/zarr_full_extent_TM_int16'):
    # constructing the monthly split
    month_split = pd.date_range(start_date, end_date, freq="MS")

    # handling date range less than a month
    if len(month_split) <= 1:
        month_split = [start_date, end_date]
        
    # identifying missing datasets in each split
    missing_datasets = [] 
    warn(f'Earliest {start_date}, latest {end_date}')
    
    for i in range(len(month_split)-1):
        # Identifying all potential datasets over specified date range
        datasets = eumetsat.identify_available_datasets(month_split[i], month_split[i+1])

        # Extracting the datetime each dataset was finished
        end_dates = [dataset['properties']['date'].split('/')[-1] for dataset in datasets]
        try:
            cleaned_end_dates = pd.to_datetime(end_dates).floor(freq='s').tz_localize('UTC').tz_convert(None)
        except:
            cleaned_end_dates = pd.to_datetime(end_dates).floor(freq='s').tz_convert(None)

        # Identifying missing datasets from the Zarr DB
        ds_eumetsat = load_from_zarr_bucket(eumetsat_zarr_bucket)
        end_dates_to_datasets = dict(zip(cleaned_end_dates, datasets))
        missing_dates = set(cleaned_end_dates) - set(pd.to_datetime(ds_eumetsat.time.values))
        missing_datasets.append([data for date, data in end_dates_to_datasets.items() if date in missing_dates])
    
    flat_list = [item for sublist in missing_datasets for item in sublist]
    
    return flat_list
```

```python
missing_datasets = identifying_missing_datasets("2020-01-01T00:00:00", "2020-01-01T01:00:00")

JSON(missing_datasets)
```

    Earliest 2020-01-01T00:00:00, latest 2020-01-01T01:00:00
    


<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:0; max-width:15ex; vertical-align:middle; text-align:right"></span>
<progress style="width:60ex" max="1" value="1" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">1/1</span>
<span class="Time-label">[00:04<00:04, 3.91s/it]</span></div>


    identify_available_datasets: found 12 results from API
    




    <IPython.core.display.JSON object>


