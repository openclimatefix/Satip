# Loading from Zarr 



```python
from satip import io

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
```

    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\google\auth\_default.py:69: UserWarning: Your application has authenticated using end user credentials from Google Cloud SDK without a quota project. You might receive a "quota exceeded" or "API not enabled" error. We recommend you rerun `gcloud auth application-default login` and make sure a quota project is added. Or you can use service accounts instead. For more information about service accounts, see https://cloud.google.com/docs/authentication/
      warnings.warn(_CLOUD_SDK_CREDENTIALS_WARNING)
    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  1.32rows/s]
    

<br>

### User Inputs

We have to specify the bucket where the data is located

```python
zarr_bucket = 'solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/full_extent_TM_int16'
```

<br>

### Loading Data

Then the `satip` wrapper for loading data will generate an `xarray` `Dataset`

```python
ds = io.load_from_zarr_bucket(zarr_bucket)

ds
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
</style><pre class='xr-text-repr-fallback'>&lt;xarray.Dataset&gt;
Dimensions:                (time: 131, variable: 12, x: 1870, y: 1831)
Coordinates:
  * time                   (time) datetime64[ns] 2020-12-16T15:19:15 ... 2020...
  * variable               (variable) object &#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;
  * x                      (x) float64 -3.088e+06 -3.084e+06 ... 4.388e+06
  * y                      (y) float64 9.012e+06 9.008e+06 ... 1.692e+06
Data variables:
    stacked_eumetsat_data  (time, x, y, variable) int16 dask.array&lt;chunksize=(36, 1870, 1831, 1), meta=np.ndarray&gt;</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.Dataset</div></div><ul class='xr-sections'><li class='xr-section-item'><input id='section-fa1d2aa3-77bf-4aff-a91b-fc5882937361' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-fa1d2aa3-77bf-4aff-a91b-fc5882937361' class='xr-section-summary'  title='Expand/collapse section'>Dimensions:</label><div class='xr-section-inline-details'><ul class='xr-dim-list'><li><span class='xr-has-index'>time</span>: 131</li><li><span class='xr-has-index'>variable</span>: 12</li><li><span class='xr-has-index'>x</span>: 1870</li><li><span class='xr-has-index'>y</span>: 1831</li></ul></div><div class='xr-section-details'></div></li><li class='xr-section-item'><input id='section-2137d184-437e-4c6a-80aa-c37dda2aaf35' class='xr-section-summary-in' type='checkbox'  checked><label for='section-2137d184-437e-4c6a-80aa-c37dda2aaf35' class='xr-section-summary' >Coordinates: <span>(4)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>time</span></div><div class='xr-var-dims'>(time)</div><div class='xr-var-dtype'>datetime64[ns]</div><div class='xr-var-preview xr-preview'>2020-12-16T15:19:15 ... 2020-12-...</div><input id='attrs-41c88be5-f26e-4345-a3a7-6a2c81958f95' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-41c88be5-f26e-4345-a3a7-6a2c81958f95' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-675232be-e27d-46b1-9f12-bd5a84f2a584' class='xr-var-data-in' type='checkbox'><label for='data-675232be-e27d-46b1-9f12-bd5a84f2a584' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;2020-12-16T15:19:15.000000000&#x27;, &#x27;2020-12-16T15:24:16.000000000&#x27;,
       &#x27;2020-12-16T15:29:17.000000000&#x27;, &#x27;2020-12-16T15:34:18.000000000&#x27;,
       &#x27;2020-12-16T15:39:18.000000000&#x27;, &#x27;2020-12-16T15:44:18.000000000&#x27;,
       &#x27;2020-12-16T15:49:18.000000000&#x27;, &#x27;2020-12-16T15:54:16.000000000&#x27;,
       &#x27;2020-12-16T15:59:15.000000000&#x27;, &#x27;2020-12-16T16:04:13.000000000&#x27;,
       &#x27;2020-12-16T16:14:13.000000000&#x27;, &#x27;2020-12-16T16:19:13.000000000&#x27;,
       &#x27;2020-12-16T16:24:14.000000000&#x27;, &#x27;2020-12-16T16:29:15.000000000&#x27;,
       &#x27;2020-12-16T16:39:16.000000000&#x27;, &#x27;2020-12-16T16:44:16.000000000&#x27;,
       &#x27;2020-12-16T16:49:16.000000000&#x27;, &#x27;2020-12-16T16:54:16.000000000&#x27;,
       &#x27;2020-12-16T16:59:15.000000000&#x27;, &#x27;2020-12-16T17:04:15.000000000&#x27;,
       &#x27;2020-12-16T17:09:15.000000000&#x27;, &#x27;2020-12-16T17:19:15.000000000&#x27;,
       &#x27;2020-12-16T17:24:16.000000000&#x27;, &#x27;2020-12-16T17:29:17.000000000&#x27;,
       &#x27;2020-12-16T17:34:18.000000000&#x27;, &#x27;2020-12-16T17:39:18.000000000&#x27;,
       &#x27;2020-12-16T21:44:18.000000000&#x27;, &#x27;2020-12-16T21:54:16.000000000&#x27;,
       &#x27;2020-12-16T21:59:16.000000000&#x27;, &#x27;2020-12-16T22:04:16.000000000&#x27;,
       &#x27;2020-12-16T22:09:16.000000000&#x27;, &#x27;2020-12-16T22:14:16.000000000&#x27;,
       &#x27;2020-12-16T22:19:15.000000000&#x27;, &#x27;2020-12-16T23:24:16.000000000&#x27;,
       &#x27;2020-12-16T23:39:18.000000000&#x27;, &#x27;2020-12-17T00:29:15.000000000&#x27;,
       &#x27;2020-12-17T00:34:15.000000000&#x27;, &#x27;2020-12-17T00:39:15.000000000&#x27;,
       &#x27;2020-12-17T00:44:15.000000000&#x27;, &#x27;2020-12-17T00:49:15.000000000&#x27;,
       &#x27;2020-12-17T00:54:16.000000000&#x27;, &#x27;2020-12-17T01:04:15.000000000&#x27;,
       &#x27;2020-12-17T01:09:15.000000000&#x27;, &#x27;2020-12-17T01:14:15.000000000&#x27;,
       &#x27;2020-12-17T01:19:15.000000000&#x27;, &#x27;2020-12-17T01:24:16.000000000&#x27;,
       &#x27;2020-12-17T01:34:18.000000000&#x27;, &#x27;2020-12-17T01:39:18.000000000&#x27;,
       &#x27;2020-12-17T01:44:18.000000000&#x27;, &#x27;2020-12-17T01:49:18.000000000&#x27;,
       &#x27;2020-12-17T01:54:16.000000000&#x27;, &#x27;2020-12-17T02:04:16.000000000&#x27;,
       &#x27;2020-12-17T02:09:16.000000000&#x27;, &#x27;2020-12-17T02:14:16.000000000&#x27;,
       &#x27;2020-12-17T02:19:15.000000000&#x27;, &#x27;2020-12-17T02:24:15.000000000&#x27;,
       &#x27;2020-12-17T02:34:15.000000000&#x27;, &#x27;2020-12-17T02:39:15.000000000&#x27;,
       &#x27;2020-12-17T02:44:15.000000000&#x27;, &#x27;2020-12-17T02:49:15.000000000&#x27;,
       &#x27;2020-12-17T02:54:16.000000000&#x27;, &#x27;2020-12-17T03:04:15.000000000&#x27;,
       &#x27;2020-12-17T03:09:15.000000000&#x27;, &#x27;2020-12-17T03:14:15.000000000&#x27;,
       &#x27;2020-12-17T03:19:15.000000000&#x27;, &#x27;2020-12-17T03:29:17.000000000&#x27;,
       &#x27;2020-12-17T03:34:18.000000000&#x27;, &#x27;2020-12-17T03:39:18.000000000&#x27;,
       &#x27;2020-12-17T03:44:18.000000000&#x27;, &#x27;2020-12-17T03:49:18.000000000&#x27;,
       &#x27;2020-12-17T03:54:16.000000000&#x27;, &#x27;2020-12-17T04:04:16.000000000&#x27;,
       &#x27;2020-12-17T04:09:16.000000000&#x27;, &#x27;2020-12-17T04:14:16.000000000&#x27;,
       &#x27;2020-12-17T04:19:15.000000000&#x27;, &#x27;2020-12-17T04:24:15.000000000&#x27;,
       &#x27;2020-12-17T04:34:15.000000000&#x27;, &#x27;2020-12-17T04:39:15.000000000&#x27;,
       &#x27;2020-12-17T04:44:15.000000000&#x27;, &#x27;2020-12-17T04:49:15.000000000&#x27;,
       &#x27;2020-12-17T04:59:15.000000000&#x27;, &#x27;2020-12-17T05:04:15.000000000&#x27;,
       &#x27;2020-12-17T05:09:15.000000000&#x27;, &#x27;2020-12-17T05:14:15.000000000&#x27;,
       &#x27;2020-12-17T05:19:15.000000000&#x27;, &#x27;2020-12-17T05:29:17.000000000&#x27;,
       &#x27;2020-12-17T05:34:18.000000000&#x27;, &#x27;2020-12-17T05:39:18.000000000&#x27;,
       &#x27;2020-12-17T05:44:18.000000000&#x27;, &#x27;2020-12-17T05:49:18.000000000&#x27;,
       &#x27;2020-12-17T05:54:16.000000000&#x27;, &#x27;2020-12-17T06:04:16.000000000&#x27;,
       &#x27;2020-12-17T06:09:16.000000000&#x27;, &#x27;2020-12-17T06:14:16.000000000&#x27;,
       &#x27;2020-12-17T06:19:16.000000000&#x27;, &#x27;2020-12-17T06:29:15.000000000&#x27;,
       &#x27;2020-12-17T06:34:15.000000000&#x27;, &#x27;2020-12-17T06:39:15.000000000&#x27;,
       &#x27;2020-12-17T06:44:15.000000000&#x27;, &#x27;2020-12-17T06:49:15.000000000&#x27;,
       &#x27;2020-12-17T06:54:16.000000000&#x27;, &#x27;2020-12-17T07:04:15.000000000&#x27;,
       &#x27;2020-12-17T07:09:15.000000000&#x27;, &#x27;2020-12-17T07:14:15.000000000&#x27;,
       &#x27;2020-12-17T07:19:15.000000000&#x27;, &#x27;2020-12-17T07:24:16.000000000&#x27;,
       &#x27;2020-12-17T07:34:18.000000000&#x27;, &#x27;2020-12-17T07:39:18.000000000&#x27;,
       &#x27;2020-12-17T07:44:18.000000000&#x27;, &#x27;2020-12-17T07:49:18.000000000&#x27;,
       &#x27;2020-12-17T07:54:16.000000000&#x27;, &#x27;2020-12-17T08:04:14.000000000&#x27;,
       &#x27;2020-12-17T08:09:13.000000000&#x27;, &#x27;2020-12-17T08:14:13.000000000&#x27;,
       &#x27;2020-12-17T08:19:13.000000000&#x27;, &#x27;2020-12-17T08:29:15.000000000&#x27;,
       &#x27;2020-12-17T08:34:16.000000000&#x27;, &#x27;2020-12-17T08:39:16.000000000&#x27;,
       &#x27;2020-12-17T08:44:16.000000000&#x27;, &#x27;2020-12-17T08:49:16.000000000&#x27;,
       &#x27;2020-12-17T08:54:16.000000000&#x27;, &#x27;2020-12-17T09:04:15.000000000&#x27;,
       &#x27;2020-12-17T09:09:15.000000000&#x27;, &#x27;2020-12-17T09:14:15.000000000&#x27;,
       &#x27;2020-12-17T09:19:15.000000000&#x27;, &#x27;2020-12-17T09:24:16.000000000&#x27;,
       &#x27;2020-12-17T09:34:18.000000000&#x27;, &#x27;2020-12-17T09:39:18.000000000&#x27;,
       &#x27;2020-12-17T09:44:18.000000000&#x27;, &#x27;2020-12-17T09:49:18.000000000&#x27;,
       &#x27;2020-12-17T09:54:16.000000000&#x27;], dtype=&#x27;datetime64[ns]&#x27;)</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>variable</span></div><div class='xr-var-dims'>(variable)</div><div class='xr-var-dtype'>object</div><div class='xr-var-preview xr-preview'>&#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;</div><input id='attrs-baf089be-1d8e-4d7e-9e64-0082ca5ef716' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-baf089be-1d8e-4d7e-9e64-0082ca5ef716' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-ce1ac32b-5e08-452d-a380-44ed436358a2' class='xr-var-data-in' type='checkbox'><label for='data-ce1ac32b-5e08-452d-a380-44ed436358a2' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;HRV&#x27;, &#x27;IR_016&#x27;, &#x27;IR_039&#x27;, &#x27;IR_087&#x27;, &#x27;IR_097&#x27;, &#x27;IR_108&#x27;, &#x27;IR_120&#x27;,
       &#x27;IR_134&#x27;, &#x27;VIS006&#x27;, &#x27;VIS008&#x27;, &#x27;WV_062&#x27;, &#x27;WV_073&#x27;], dtype=object)</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>-3.088e+06 -3.084e+06 ... 4.388e+06</div><input id='attrs-a60fabb7-29ed-4277-8dc9-9dfea419f9c8' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-a60fabb7-29ed-4277-8dc9-9dfea419f9c8' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-e0b46b57-d317-448c-96dd-1c0793c09c22' class='xr-var-data-in' type='checkbox'><label for='data-e0b46b57-d317-448c-96dd-1c0793c09c22' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([-3088000., -3084000., -3080000., ...,  4380000.,  4384000.,  4388000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>9.012e+06 9.008e+06 ... 1.692e+06</div><input id='attrs-320903cf-beb5-4ddd-b766-d5b5a33c7ba4' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-320903cf-beb5-4ddd-b766-d5b5a33c7ba4' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-ac697240-5df5-4358-b297-054c0e95a980' class='xr-var-data-in' type='checkbox'><label for='data-ac697240-5df5-4358-b297-054c0e95a980' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([9012000., 9008000., 9004000., ..., 1700000., 1696000., 1692000.])</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-8ba4f01b-5205-4401-897e-7c2148363ded' class='xr-section-summary-in' type='checkbox'  checked><label for='section-8ba4f01b-5205-4401-897e-7c2148363ded' class='xr-section-summary' >Data variables: <span>(1)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span>stacked_eumetsat_data</span></div><div class='xr-var-dims'>(time, x, y, variable)</div><div class='xr-var-dtype'>int16</div><div class='xr-var-preview xr-preview'>dask.array&lt;chunksize=(36, 1870, 1831, 1), meta=np.ndarray&gt;</div><input id='attrs-fe069c56-7ac9-4c2a-b9d4-a033e92767b8' class='xr-var-attrs-in' type='checkbox' ><label for='attrs-fe069c56-7ac9-4c2a-b9d4-a033e92767b8' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-67ea7e38-01fb-4ae1-b07f-dc44331f0f3b' class='xr-var-data-in' type='checkbox'><label for='data-67ea7e38-01fb-4ae1-b07f-dc44331f0f3b' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'><dt><span>meta :</span></dt><dd>{&#x27;orbital_parameters&#x27;: {&#x27;projection_longitude&#x27;: 9.5, &#x27;projection_latitude&#x27;: 0.0, &#x27;projection_altitude&#x27;: 35785831.0}, &#x27;sun_earth_distance_correction_applied&#x27;: True, &#x27;sun_earth_distance_correction_factor&#x27;: 0.9680594019679534, &#x27;units&#x27;: &#x27;%&#x27;, &#x27;wavelength&#x27;: WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), &#x27;standard_name&#x27;: &#x27;toa_bidirectional_reflectance&#x27;, &#x27;platform_name&#x27;: &#x27;Meteosat-10&#x27;, &#x27;sensor&#x27;: &#x27;seviri&#x27;, &#x27;start_time&#x27;: datetime.datetime(2020, 12, 16, 15, 15, 8, 939946), &#x27;end_time&#x27;: datetime.datetime(2020, 12, 16, 15, 20, 9, 986974), &#x27;area&#x27;: Area ID: geos_seviri_hrv
Description: SEVIRI high resolution channel area
Projection ID: seviri_hrv
Projection: {&#x27;a&#x27;: &#x27;6378169&#x27;, &#x27;h&#x27;: &#x27;35785831&#x27;, &#x27;lon_0&#x27;: &#x27;9.5&#x27;, &#x27;no_defs&#x27;: &#x27;None&#x27;, &#x27;proj&#x27;: &#x27;geos&#x27;, &#x27;rf&#x27;: &#x27;295.488065897014&#x27;, &#x27;type&#x27;: &#x27;crs&#x27;, &#x27;units&#x27;: &#x27;m&#x27;, &#x27;x_0&#x27;: &#x27;0&#x27;, &#x27;y_0&#x27;: &#x27;0&#x27;}
Number of columns: 5568
Number of rows: 4176
Area extent: (2806877.0501, 5571248.3904, -2761871.0044, 1394687.3495), &#x27;name&#x27;: &#x27;HRV&#x27;, &#x27;resolution&#x27;: 1000.134348869, &#x27;calibration&#x27;: &#x27;reflectance&#x27;, &#x27;modifiers&#x27;: (), &#x27;_satpy_id&#x27;: DataID(name=&#x27;HRV&#x27;, wavelength=WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), resolution=1000.134348869, calibration=&lt;calibration.reflectance&gt;, modifiers=()), &#x27;ancillary_variables&#x27;: []}</dd></dl></div><div class='xr-var-data'><table>
<tr>
<td>
<table>
  <thead>
    <tr><td> </td><th> Array </th><th> Chunk </th></tr>
  </thead>
  <tbody>
    <tr><th> Bytes </th><td> 10.76 GB </td> <td> 246.53 MB </td></tr>
    <tr><th> Shape </th><td> (131, 1870, 1831, 12) </td> <td> (36, 1870, 1831, 1) </td></tr>
    <tr><th> Count </th><td> 49 Tasks </td><td> 48 Chunks </td></tr>
    <tr><th> Type </th><td> int16 </td><td> numpy.ndarray </td></tr>
  </tbody>
</table>
</td>
<td>
<svg width="358" height="238" style="stroke:rgb(0,0,0);stroke-width:1" >

  <!-- Horizontal lines -->
  <line x1="0" y1="0" x2="36" y2="0" style="stroke-width:2" />
  <line x1="0" y1="25" x2="36" y2="25" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="0" y1="0" x2="0" y2="25" style="stroke-width:2" />
  <line x1="10" y1="0" x2="10" y2="25" />
  <line x1="20" y1="0" x2="20" y2="25" />
  <line x1="30" y1="0" x2="30" y2="25" />
  <line x1="36" y1="0" x2="36" y2="25" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="0.0,0.0 36.54392367482379,0.0 36.54392367482379,25.412616514582485 0.0,25.412616514582485" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Text -->
  <text x="18.271962" y="45.412617" font-size="1.0rem" font-weight="100" text-anchor="middle" >131</text>
  <text x="56.543924" y="12.706308" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(0,56.543924,12.706308)">1</text>


  <!-- Horizontal lines -->
  <line x1="106" y1="0" x2="176" y2="70" style="stroke-width:2" />
  <line x1="106" y1="117" x2="176" y2="188" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="106" y1="0" x2="106" y2="117" style="stroke-width:2" />
  <line x1="176" y1="70" x2="176" y2="188" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="106.0,0.0 176.58823529411765,70.58823529411765 176.58823529411765,188.0855614973262 106.0,117.49732620320856" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="106" y1="0" x2="131" y2="0" style="stroke-width:2" />
  <line x1="176" y1="70" x2="202" y2="70" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="106" y1="0" x2="176" y2="70" style="stroke-width:2" />
  <line x1="108" y1="0" x2="178" y2="70" />
  <line x1="110" y1="0" x2="180" y2="70" />
  <line x1="112" y1="0" x2="182" y2="70" />
  <line x1="114" y1="0" x2="185" y2="70" />
  <line x1="116" y1="0" x2="187" y2="70" />
  <line x1="118" y1="0" x2="189" y2="70" />
  <line x1="120" y1="0" x2="191" y2="70" />
  <line x1="122" y1="0" x2="193" y2="70" />
  <line x1="125" y1="0" x2="195" y2="70" />
  <line x1="127" y1="0" x2="197" y2="70" />
  <line x1="129" y1="0" x2="199" y2="70" />
  <line x1="131" y1="0" x2="202" y2="70" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="106.0,0.0 131.41261651458248,0.0 202.00085180870013,70.58823529411765 176.58823529411765,70.58823529411765" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="176" y1="70" x2="202" y2="70" style="stroke-width:2" />
  <line x1="176" y1="188" x2="202" y2="188" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="176" y1="70" x2="176" y2="188" style="stroke-width:2" />
  <line x1="178" y1="70" x2="178" y2="188" />
  <line x1="180" y1="70" x2="180" y2="188" />
  <line x1="182" y1="70" x2="182" y2="188" />
  <line x1="185" y1="70" x2="185" y2="188" />
  <line x1="187" y1="70" x2="187" y2="188" />
  <line x1="189" y1="70" x2="189" y2="188" />
  <line x1="191" y1="70" x2="191" y2="188" />
  <line x1="193" y1="70" x2="193" y2="188" />
  <line x1="195" y1="70" x2="195" y2="188" />
  <line x1="197" y1="70" x2="197" y2="188" />
  <line x1="199" y1="70" x2="199" y2="188" />
  <line x1="202" y1="70" x2="202" y2="188" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="176.58823529411765,70.58823529411765 202.00085180870013,70.58823529411765 202.00085180870013,188.0855614973262 176.58823529411765,188.0855614973262" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Text -->
  <text x="189.294544" y="208.085561" font-size="1.0rem" font-weight="100" text-anchor="middle" >12</text>
  <text x="222.000852" y="129.336898" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(-90,222.000852,129.336898)">1831</text>
  <text x="131.294118" y="172.791444" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(45,131.294118,172.791444)">1870</text>
</svg>
</td>
</tr>
</table></div></li></ul></div></li><li class='xr-section-item'><input id='section-d7e58fef-2c82-4815-ab61-a1c58e7e2d42' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-d7e58fef-2c82-4815-ab61-a1c58e7e2d42' class='xr-section-summary'  title='Expand/collapse section'>Attributes: <span>(0)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'></dl></div></li></ul></div></div>



<br>

We can then index this as we would any other `xarray` object

```python
da_HRV_sample = ds['stacked_eumetsat_data'].isel(time=0).sel(variable='HRV')

da_HRV_sample
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
</style><pre class='xr-text-repr-fallback'>&lt;xarray.DataArray &#x27;stacked_eumetsat_data&#x27; (x: 1870, y: 1831)&gt;
dask.array&lt;getitem, shape=(1870, 1831), dtype=int16, chunksize=(1870, 1831), chunktype=numpy.ndarray&gt;
Coordinates:
    time      datetime64[ns] 2020-12-16T15:19:15
    variable  &lt;U3 &#x27;HRV&#x27;
  * x         (x) float64 -3.088e+06 -3.084e+06 ... 4.384e+06 4.388e+06
  * y         (y) float64 9.012e+06 9.008e+06 9.004e+06 ... 1.696e+06 1.692e+06
Attributes:
    meta:     {&#x27;orbital_parameters&#x27;: {&#x27;projection_longitude&#x27;: 9.5, &#x27;projectio...</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.DataArray</div><div class='xr-array-name'>'stacked_eumetsat_data'</div><ul class='xr-dim-list'><li><span class='xr-has-index'>x</span>: 1870</li><li><span class='xr-has-index'>y</span>: 1831</li></ul></div><ul class='xr-sections'><li class='xr-section-item'><div class='xr-array-wrap'><input id='section-d87fd08a-7de2-4b4f-bb58-f4052823a942' class='xr-array-in' type='checkbox' checked><label for='section-d87fd08a-7de2-4b4f-bb58-f4052823a942' title='Show/hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-array-preview xr-preview'><span>dask.array&lt;chunksize=(1870, 1831), meta=np.ndarray&gt;</span></div><div class='xr-array-data'><table>
<tr>
<td>
<table>
  <thead>
    <tr><td> </td><th> Array </th><th> Chunk </th></tr>
  </thead>
  <tbody>
    <tr><th> Bytes </th><td> 6.85 MB </td> <td> 6.85 MB </td></tr>
    <tr><th> Shape </th><td> (1870, 1831) </td> <td> (1870, 1831) </td></tr>
    <tr><th> Count </th><td> 62 Tasks </td><td> 1 Chunks </td></tr>
    <tr><th> Type </th><td> int16 </td><td> numpy.ndarray </td></tr>
  </tbody>
</table>
</td>
<td>
<svg width="167" height="170" style="stroke:rgb(0,0,0);stroke-width:1" >

  <!-- Horizontal lines -->
  <line x1="0" y1="0" x2="117" y2="0" style="stroke-width:2" />
  <line x1="0" y1="120" x2="117" y2="120" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="0" y1="0" x2="0" y2="120" style="stroke-width:2" />
  <line x1="117" y1="0" x2="117" y2="120" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="0.0,0.0 117.49732620320856,0.0 117.49732620320856,120.0 0.0,120.0" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Text -->
  <text x="58.748663" y="140.000000" font-size="1.0rem" font-weight="100" text-anchor="middle" >1831</text>
  <text x="137.497326" y="60.000000" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(-90,137.497326,60.000000)">1870</text>
</svg>
</td>
</tr>
</table></div></div></li><li class='xr-section-item'><input id='section-dbd6ccbc-c8c6-4e04-be6f-90633dd15ad7' class='xr-section-summary-in' type='checkbox'  checked><label for='section-dbd6ccbc-c8c6-4e04-be6f-90633dd15ad7' class='xr-section-summary' >Coordinates: <span>(4)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span>time</span></div><div class='xr-var-dims'>()</div><div class='xr-var-dtype'>datetime64[ns]</div><div class='xr-var-preview xr-preview'>2020-12-16T15:19:15</div><input id='attrs-27631c2e-02b9-4363-8847-a12bb53cebac' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-27631c2e-02b9-4363-8847-a12bb53cebac' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-1d66a9d9-474e-44fa-ad69-9df99f573d6e' class='xr-var-data-in' type='checkbox'><label for='data-1d66a9d9-474e-44fa-ad69-9df99f573d6e' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array(&#x27;2020-12-16T15:19:15.000000000&#x27;, dtype=&#x27;datetime64[ns]&#x27;)</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span>variable</span></div><div class='xr-var-dims'>()</div><div class='xr-var-dtype'>&lt;U3</div><div class='xr-var-preview xr-preview'>&#x27;HRV&#x27;</div><input id='attrs-ba472e60-e440-49af-a090-8334bd971fe6' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-ba472e60-e440-49af-a090-8334bd971fe6' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-3a497cf2-617c-4da2-ba01-e6cb61c06d9e' class='xr-var-data-in' type='checkbox'><label for='data-3a497cf2-617c-4da2-ba01-e6cb61c06d9e' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array(&#x27;HRV&#x27;, dtype=&#x27;&lt;U3&#x27;)</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>-3.088e+06 -3.084e+06 ... 4.388e+06</div><input id='attrs-9fe38d0e-bfa7-4b88-ac89-c174ce7a4b4d' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-9fe38d0e-bfa7-4b88-ac89-c174ce7a4b4d' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-7e9761e6-f476-4176-aba0-53cbaab59b06' class='xr-var-data-in' type='checkbox'><label for='data-7e9761e6-f476-4176-aba0-53cbaab59b06' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([-3088000., -3084000., -3080000., ...,  4380000.,  4384000.,  4388000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>9.012e+06 9.008e+06 ... 1.692e+06</div><input id='attrs-96e19d5b-8f41-4fb6-be32-8d6c5f65a80d' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-96e19d5b-8f41-4fb6-be32-8d6c5f65a80d' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-ffa662db-afe6-4517-9087-7c38e9eed1bc' class='xr-var-data-in' type='checkbox'><label for='data-ffa662db-afe6-4517-9087-7c38e9eed1bc' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([9012000., 9008000., 9004000., ..., 1700000., 1696000., 1692000.])</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-2cfe85a8-21b7-45f1-a8e1-3fbaacdcef9c' class='xr-section-summary-in' type='checkbox'  checked><label for='section-2cfe85a8-21b7-45f1-a8e1-3fbaacdcef9c' class='xr-section-summary' >Attributes: <span>(1)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'><dt><span>meta :</span></dt><dd>{&#x27;orbital_parameters&#x27;: {&#x27;projection_longitude&#x27;: 9.5, &#x27;projection_latitude&#x27;: 0.0, &#x27;projection_altitude&#x27;: 35785831.0}, &#x27;sun_earth_distance_correction_applied&#x27;: True, &#x27;sun_earth_distance_correction_factor&#x27;: 0.9680594019679534, &#x27;units&#x27;: &#x27;%&#x27;, &#x27;wavelength&#x27;: WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), &#x27;standard_name&#x27;: &#x27;toa_bidirectional_reflectance&#x27;, &#x27;platform_name&#x27;: &#x27;Meteosat-10&#x27;, &#x27;sensor&#x27;: &#x27;seviri&#x27;, &#x27;start_time&#x27;: datetime.datetime(2020, 12, 16, 15, 15, 8, 939946), &#x27;end_time&#x27;: datetime.datetime(2020, 12, 16, 15, 20, 9, 986974), &#x27;area&#x27;: Area ID: geos_seviri_hrv
Description: SEVIRI high resolution channel area
Projection ID: seviri_hrv
Projection: {&#x27;a&#x27;: &#x27;6378169&#x27;, &#x27;h&#x27;: &#x27;35785831&#x27;, &#x27;lon_0&#x27;: &#x27;9.5&#x27;, &#x27;no_defs&#x27;: &#x27;None&#x27;, &#x27;proj&#x27;: &#x27;geos&#x27;, &#x27;rf&#x27;: &#x27;295.488065897014&#x27;, &#x27;type&#x27;: &#x27;crs&#x27;, &#x27;units&#x27;: &#x27;m&#x27;, &#x27;x_0&#x27;: &#x27;0&#x27;, &#x27;y_0&#x27;: &#x27;0&#x27;}
Number of columns: 5568
Number of rows: 4176
Area extent: (2806877.0501, 5571248.3904, -2761871.0044, 1394687.3495), &#x27;name&#x27;: &#x27;HRV&#x27;, &#x27;resolution&#x27;: 1000.134348869, &#x27;calibration&#x27;: &#x27;reflectance&#x27;, &#x27;modifiers&#x27;: (), &#x27;_satpy_id&#x27;: DataID(name=&#x27;HRV&#x27;, wavelength=WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), resolution=1000.134348869, calibration=&lt;calibration.reflectance&gt;, modifiers=()), &#x27;ancillary_variables&#x27;: []}</dd></dl></div></li></ul></div></div>



<br>

As well as visualise it, here we'll use `cartopy` to plot the data with a coastline overlay.

The darker area on the right hand side of the image are the areas where the sun has already set.

```python
fig = plt.figure(dpi=250, figsize=(10, 10))
ax = plt.axes(projection=ccrs.TransverseMercator())

da_HRV_sample.T.plot.imshow(ax=ax, cmap='magma', vmin=-200, vmax=400)

ax.coastlines(resolution='50m', alpha=0.8, color='white')
```

    <ipython-input-8-5badebb6746d>:2: UserWarning: The default value for the *approx* keyword argument to TransverseMercator will change from True to False after 0.18.
      ax = plt.axes(projection=ccrs.TransverseMercator())
    




    <cartopy.mpl.feature_artist.FeatureArtist at 0x201ef3a5b20>




![png](img/nbs/output_8_2.png)

