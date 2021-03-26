# Zarr Database Summary & Validation



```python
import numpy as np
import pandas as pd

from satip import io

import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import FEAutils as hlp
from warnings import warn
from ipypb import track
```

    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\google\auth\_default.py:69: UserWarning: Your application has authenticated using end user credentials from Google Cloud SDK without a quota project. You might receive a "quota exceeded" or "API not enabled" error. We recommend you rerun `gcloud auth application-default login` and make sure a quota project is added. Or you can use service accounts instead. For more information about service accounts, see https://cloud.google.com/docs/authentication/
      warnings.warn(_CLOUD_SDK_CREDENTIALS_WARNING)
    Downloading: 100%|â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ| 1/1 [00:00<00:00,  1.23rows/s]
    

<br>

### User Inputs

We have to specify the bucket where the data is located

```python
zarr_bucket = 'solar-pv-nowcasting-data/satellite/EUMETSAT/SEVIRI_RSS/zarr_full_extent_TM_int16'
```

<br>

### Data Loading & Coverage

The `satip` wrapper for loading data will then generate an `xarray` `Dataset` when passed the path to the zarr bucket

```python
ds = io.load_from_zarr_bucket(zarr_bucket)

ds['stacked_eumetsat_data']
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
</style><pre class='xr-text-repr-fallback'>&lt;xarray.DataArray &#x27;stacked_eumetsat_data&#x27; (time: 11652, x: 1870, y: 1831, variable: 12)&gt;
dask.array&lt;xarray-stacked_eumetsat_data, shape=(11652, 1870, 1831, 12), dtype=int16, chunksize=(36, 1870, 1831, 1), chunktype=numpy.ndarray&gt;
Coordinates:
  * time      (time) datetime64[ns] 2021-03-19T13:20:10 ... 2020-04-04T06:19:16
  * variable  (variable) object &#x27;HRV&#x27; &#x27;IR_016&#x27; &#x27;IR_039&#x27; ... &#x27;WV_062&#x27; &#x27;WV_073&#x27;
  * x         (x) float64 -3.088e+06 -3.084e+06 ... 4.384e+06 4.388e+06
  * y         (y) float64 9.012e+06 9.008e+06 9.004e+06 ... 1.696e+06 1.692e+06
Attributes:
    meta:     {&#x27;orbital_parameters&#x27;: {&#x27;projection_longitude&#x27;: 9.5, &#x27;projectio...</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.DataArray</div><div class='xr-array-name'>'stacked_eumetsat_data'</div><ul class='xr-dim-list'><li><span class='xr-has-index'>time</span>: 11652</li><li><span class='xr-has-index'>x</span>: 1870</li><li><span class='xr-has-index'>y</span>: 1831</li><li><span class='xr-has-index'>variable</span>: 12</li></ul></div><ul class='xr-sections'><li class='xr-section-item'><div class='xr-array-wrap'><input id='section-3c5a9c4a-62a0-428e-8adb-d5145991f89c' class='xr-array-in' type='checkbox' checked><label for='section-3c5a9c4a-62a0-428e-8adb-d5145991f89c' title='Show/hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-array-preview xr-preview'><span>dask.array&lt;chunksize=(36, 1870, 1831, 1), meta=np.ndarray&gt;</span></div><div class='xr-array-data'><table>
<tr>
<td>
<table>
  <thead>
    <tr><td> </td><th> Array </th><th> Chunk </th></tr>
  </thead>
  <tbody>
    <tr><th> Bytes </th><td> 957.51 GB </td> <td> 246.53 MB </td></tr>
    <tr><th> Shape </th><td> (11652, 1870, 1831, 12) </td> <td> (36, 1870, 1831, 1) </td></tr>
    <tr><th> Count </th><td> 3889 Tasks </td><td> 3888 Chunks </td></tr>
    <tr><th> Type </th><td> int16 </td><td> numpy.ndarray </td></tr>
  </tbody>
</table>
</td>
<td>
<svg width="479" height="115" style="stroke:rgb(0,0,0);stroke-width:1" >

  <!-- Horizontal lines -->
  <line x1="0" y1="0" x2="120" y2="0" style="stroke-width:2" />
  <line x1="0" y1="25" x2="120" y2="25" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="0" y1="0" x2="0" y2="25" style="stroke-width:2" />
  <line x1="3" y1="0" x2="3" y2="25" />
  <line x1="7" y1="0" x2="7" y2="25" />
  <line x1="11" y1="0" x2="11" y2="25" />
  <line x1="14" y1="0" x2="14" y2="25" />
  <line x1="18" y1="0" x2="18" y2="25" />
  <line x1="22" y1="0" x2="22" y2="25" />
  <line x1="25" y1="0" x2="25" y2="25" />
  <line x1="30" y1="0" x2="30" y2="25" />
  <line x1="33" y1="0" x2="33" y2="25" />
  <line x1="37" y1="0" x2="37" y2="25" />
  <line x1="41" y1="0" x2="41" y2="25" />
  <line x1="44" y1="0" x2="44" y2="25" />
  <line x1="48" y1="0" x2="48" y2="25" />
  <line x1="52" y1="0" x2="52" y2="25" />
  <line x1="55" y1="0" x2="55" y2="25" />
  <line x1="60" y1="0" x2="60" y2="25" />
  <line x1="63" y1="0" x2="63" y2="25" />
  <line x1="67" y1="0" x2="67" y2="25" />
  <line x1="71" y1="0" x2="71" y2="25" />
  <line x1="74" y1="0" x2="74" y2="25" />
  <line x1="78" y1="0" x2="78" y2="25" />
  <line x1="82" y1="0" x2="82" y2="25" />
  <line x1="86" y1="0" x2="86" y2="25" />
  <line x1="90" y1="0" x2="90" y2="25" />
  <line x1="93" y1="0" x2="93" y2="25" />
  <line x1="97" y1="0" x2="97" y2="25" />
  <line x1="101" y1="0" x2="101" y2="25" />
  <line x1="104" y1="0" x2="104" y2="25" />
  <line x1="108" y1="0" x2="108" y2="25" />
  <line x1="112" y1="0" x2="112" y2="25" />
  <line x1="116" y1="0" x2="116" y2="25" />
  <line x1="120" y1="0" x2="120" y2="25" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="0.0,0.0 120.0,0.0 120.0,25.412616514582485 0.0,25.412616514582485" style="fill:#8B4903A0;stroke-width:0"/>

  <!-- Text -->
  <text x="60.000000" y="45.412617" font-size="1.0rem" font-weight="100" text-anchor="middle" >11652</text>
  <text x="140.000000" y="12.706308" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(0,140.000000,12.706308)">1</text>


  <!-- Horizontal lines -->
  <line x1="190" y1="0" x2="214" y2="24" style="stroke-width:2" />
  <line x1="190" y1="40" x2="214" y2="65" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="190" y1="0" x2="190" y2="40" style="stroke-width:2" />
  <line x1="214" y1="24" x2="214" y2="65" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="190.0,0.0 214.13415148675503,24.134151486755034 214.13415148675503,65.0628781439491 190.0,40.92872665719407" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="190" y1="0" x2="215" y2="0" style="stroke-width:2" />
  <line x1="214" y1="24" x2="239" y2="24" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="190" y1="0" x2="214" y2="24" style="stroke-width:2" />
  <line x1="192" y1="0" x2="216" y2="24" />
  <line x1="194" y1="0" x2="218" y2="24" />
  <line x1="196" y1="0" x2="220" y2="24" />
  <line x1="198" y1="0" x2="222" y2="24" />
  <line x1="200" y1="0" x2="224" y2="24" />
  <line x1="202" y1="0" x2="226" y2="24" />
  <line x1="204" y1="0" x2="228" y2="24" />
  <line x1="206" y1="0" x2="231" y2="24" />
  <line x1="209" y1="0" x2="233" y2="24" />
  <line x1="211" y1="0" x2="235" y2="24" />
  <line x1="213" y1="0" x2="237" y2="24" />
  <line x1="215" y1="0" x2="239" y2="24" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="190.0,0.0 215.41261651458248,0.0 239.5467680013375,24.134151486755034 214.13415148675503,24.134151486755034" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Horizontal lines -->
  <line x1="214" y1="24" x2="239" y2="24" style="stroke-width:2" />
  <line x1="214" y1="65" x2="239" y2="65" style="stroke-width:2" />

  <!-- Vertical lines -->
  <line x1="214" y1="24" x2="214" y2="65" style="stroke-width:2" />
  <line x1="216" y1="24" x2="216" y2="65" />
  <line x1="218" y1="24" x2="218" y2="65" />
  <line x1="220" y1="24" x2="220" y2="65" />
  <line x1="222" y1="24" x2="222" y2="65" />
  <line x1="224" y1="24" x2="224" y2="65" />
  <line x1="226" y1="24" x2="226" y2="65" />
  <line x1="228" y1="24" x2="228" y2="65" />
  <line x1="231" y1="24" x2="231" y2="65" />
  <line x1="233" y1="24" x2="233" y2="65" />
  <line x1="235" y1="24" x2="235" y2="65" />
  <line x1="237" y1="24" x2="237" y2="65" />
  <line x1="239" y1="24" x2="239" y2="65" style="stroke-width:2" />

  <!-- Colored Rectangle -->
  <polygon points="214.13415148675503,24.134151486755034 239.5467680013375,24.134151486755034 239.5467680013375,65.0628781439491 214.13415148675503,65.0628781439491" style="fill:#ECB172A0;stroke-width:0"/>

  <!-- Text -->
  <text x="226.840460" y="85.062878" font-size="1.0rem" font-weight="100" text-anchor="middle" >12</text>
  <text x="259.546768" y="44.598515" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(-90,259.546768,44.598515)">1831</text>
  <text x="192.067076" y="72.995802" font-size="1.0rem" font-weight="100" text-anchor="middle" transform="rotate(45,192.067076,72.995802)">1870</text>
</svg>
</td>
</tr>
</table></div></div></li><li class='xr-section-item'><input id='section-64abfc14-fb7a-4158-8ab6-b7524ef6fc40' class='xr-section-summary-in' type='checkbox'  checked><label for='section-64abfc14-fb7a-4158-8ab6-b7524ef6fc40' class='xr-section-summary' >Coordinates: <span>(4)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>time</span></div><div class='xr-var-dims'>(time)</div><div class='xr-var-dtype'>datetime64[ns]</div><div class='xr-var-preview xr-preview'>2021-03-19T13:20:10 ... 2020-04-...</div><input id='attrs-615ad838-dc2c-41e5-884b-9d7b551073a8' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-615ad838-dc2c-41e5-884b-9d7b551073a8' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-d4478c3b-391b-45d3-8605-e92b9fce0218' class='xr-var-data-in' type='checkbox'><label for='data-d4478c3b-391b-45d3-8605-e92b9fce0218' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;2021-03-19T13:20:10.000000000&#x27;, &#x27;2021-03-19T13:24:16.000000000&#x27;,
       &#x27;2021-03-19T13:29:17.000000000&#x27;, ..., &#x27;2020-04-04T06:09:17.000000000&#x27;,
       &#x27;2020-04-04T06:14:17.000000000&#x27;, &#x27;2020-04-04T06:19:16.000000000&#x27;],
      dtype=&#x27;datetime64[ns]&#x27;)</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>variable</span></div><div class='xr-var-dims'>(variable)</div><div class='xr-var-dtype'>object</div><div class='xr-var-preview xr-preview'>&#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;</div><input id='attrs-39c8ff72-fe72-4014-8368-a874bd35d6b1' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-39c8ff72-fe72-4014-8368-a874bd35d6b1' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-7538a1b4-fb51-4e01-80f3-d0ed365f953d' class='xr-var-data-in' type='checkbox'><label for='data-7538a1b4-fb51-4e01-80f3-d0ed365f953d' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;HRV&#x27;, &#x27;IR_016&#x27;, &#x27;IR_039&#x27;, &#x27;IR_087&#x27;, &#x27;IR_097&#x27;, &#x27;IR_108&#x27;, &#x27;IR_120&#x27;,
       &#x27;IR_134&#x27;, &#x27;VIS006&#x27;, &#x27;VIS008&#x27;, &#x27;WV_062&#x27;, &#x27;WV_073&#x27;], dtype=object)</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>-3.088e+06 -3.084e+06 ... 4.388e+06</div><input id='attrs-d70aeda3-a440-446c-ac09-322639698ea1' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-d70aeda3-a440-446c-ac09-322639698ea1' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-e8dd9b88-db3a-49c2-9afa-2783537a3f94' class='xr-var-data-in' type='checkbox'><label for='data-e8dd9b88-db3a-49c2-9afa-2783537a3f94' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([-3088000., -3084000., -3080000., ...,  4380000.,  4384000.,  4388000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>9.012e+06 9.008e+06 ... 1.692e+06</div><input id='attrs-964915e2-982b-4bb9-838a-09860524300c' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-964915e2-982b-4bb9-838a-09860524300c' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-c9b52c27-98fa-4792-8a45-80c8479841e1' class='xr-var-data-in' type='checkbox'><label for='data-c9b52c27-98fa-4792-8a45-80c8479841e1' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([9012000., 9008000., 9004000., ..., 1700000., 1696000., 1692000.])</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-d4050408-8f4d-439b-b1ac-ae1c1563e2ab' class='xr-section-summary-in' type='checkbox'  checked><label for='section-d4050408-8f4d-439b-b1ac-ae1c1563e2ab' class='xr-section-summary' >Attributes: <span>(1)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'><dt><span>meta :</span></dt><dd>{&#x27;orbital_parameters&#x27;: {&#x27;projection_longitude&#x27;: 9.5, &#x27;projection_latitude&#x27;: 0.0, &#x27;projection_altitude&#x27;: 35785831.0}, &#x27;sun_earth_distance_correction_applied&#x27;: True, &#x27;sun_earth_distance_correction_factor&#x27;: 0.9911189780118609, &#x27;units&#x27;: &#x27;%&#x27;, &#x27;wavelength&#x27;: WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), &#x27;standard_name&#x27;: &#x27;toa_bidirectional_reflectance&#x27;, &#x27;platform_name&#x27;: &#x27;Meteosat-10&#x27;, &#x27;sensor&#x27;: &#x27;seviri&#x27;, &#x27;start_time&#x27;: datetime.datetime(2021, 3, 19, 13, 15, 9, 278906), &#x27;end_time&#x27;: datetime.datetime(2021, 3, 19, 13, 20, 10, 330158), &#x27;area&#x27;: Area ID: geos_seviri_hrv
Description: SEVIRI high resolution channel area
Projection ID: seviri_hrv
Projection: {&#x27;a&#x27;: &#x27;6378169&#x27;, &#x27;h&#x27;: &#x27;35785831&#x27;, &#x27;lon_0&#x27;: &#x27;9.5&#x27;, &#x27;no_defs&#x27;: &#x27;None&#x27;, &#x27;proj&#x27;: &#x27;geos&#x27;, &#x27;rf&#x27;: &#x27;295.488065897014&#x27;, &#x27;type&#x27;: &#x27;crs&#x27;, &#x27;units&#x27;: &#x27;m&#x27;, &#x27;x_0&#x27;: &#x27;0&#x27;, &#x27;y_0&#x27;: &#x27;0&#x27;}
Number of columns: 5568
Number of rows: 4176
Area extent: (2790874.9005, 5571248.3904, -2777873.154, 1394687.3495), &#x27;name&#x27;: &#x27;HRV&#x27;, &#x27;resolution&#x27;: 1000.134348869, &#x27;calibration&#x27;: &#x27;reflectance&#x27;, &#x27;modifiers&#x27;: (), &#x27;_satpy_id&#x27;: DataID(name=&#x27;HRV&#x27;, wavelength=WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), resolution=1000.134348869, calibration=&lt;calibration.reflectance&gt;, modifiers=()), &#x27;ancillary_variables&#x27;: []}</dd></dl></div></li></ul></div></div>



<br>

We'll quickly visualise the data coverage that's provided in the database.

N.b. Here we've made the assumption that an image is generated every 5 minutes.

```python
round_dt_idx = lambda dt_idx: pd.to_datetime(((dt_idx.astype(np.int64) // ns5min + 1 ) * ns5min))

ns5min = 5*60*1000000000

zarr_db_dts = pd.to_datetime(ds['stacked_eumetsat_data'].time.values)
dt_rng_5m = round_dt_idx(pd.date_range(zarr_db_dts.min(), zarr_db_dts.max(), freq='5T'))

s_db_coverage = pd.Series(round_dt_idx(zarr_db_dts)).value_counts().reindex(dt_rng_5m)
current_db_coverage = 1 - s_db_coverage.isnull().mean()

print(f'The database coverage is currently at {100*current_db_coverage:.1f}%')

# Plotting
fig, ax = plt.subplots(dpi=150)

s_db_coverage.resample('D').sum().pipe(lambda s: 100*s/s.max()).plot.area(ax=ax)

ax.set_ylim(0, 100)
ax.set_ylabel('Database Coverage (%)')
hlp.hide_spines(ax)
```

    The database coverage is currently at 5.0%
    


![png](img/nbs/output_6_1.png)


<br>

We'll create a slightly modified version of this that doesn't show percentage coverage for each day but instead considers each 5 minute period and groups batches of data that were retrieved sequentially 

```python
#exports
def extract_dt_batch_sets(zarr_db_dts):
    dt_rng_split_idxs = (pd.Series(zarr_db_dts).diff(1).dt.total_seconds().abs() > (5 * 60 * 2)).replace(False, np.nan).dropna().index

    dt_batch_start_idxs = [0] + list(dt_rng_split_idxs)
    dt_batch_end_idxs = list(dt_rng_split_idxs-1) + [len(zarr_db_dts)-1]

    dt_batches = []

    for dt_batch_start_idx, dt_batch_end_idx in zip(dt_batch_start_idxs, dt_batch_end_idxs):
        dt_batches += [(zarr_db_dts[dt_batch_start_idx], zarr_db_dts[dt_batch_end_idx])]
        
    return dt_batches
```

```python
dt_batches = extract_dt_batch_sets(zarr_db_dts)

# Plotting
fig, ax = plt.subplots(dpi=150)

cmap = mpl.cm.get_cmap('magma')
total_dts_processed = 0

for batch_start_dt, batch_end_dt in track(dt_batches):
    if batch_start_dt == batch_end_dt:
        s_db_batch = pd.Series([1, 1], index=[batch_start_dt, batch_start_dt+pd.Timedelta(minutes=5)])
        total_dts_processed += 1
        batch_mid_pct_processed = total_dts_processed/zarr_db_dts.size
    else:
        s_db_batch = s_db_coverage[batch_start_dt:batch_end_dt]
        total_dts_processed += s_db_batch.size
        batch_mid_pct_processed = (total_dts_processed-(s_db_batch.size/2))/zarr_db_dts.size
        
    color = cmap(batch_mid_pct_processed)
    s_db_batch.plot.area(color=color, ax=ax)
    
ax.set_xlim(zarr_db_dts.min(), zarr_db_dts.max())
ax.set_ylim(0, 1)
hlp.hide_spines(ax)
```


<div><span class="Text-label" style="display:inline-block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:0; max-width:15ex; vertical-align:middle; text-align:right"></span>
<progress style="width:60ex" max="62" value="62" class="Progress-main"/></progress>
<span class="Progress-label"><strong>100%</strong></span>
<span class="Iteration-label">62/62</span>
<span class="Time-label">[06:28<00:10, 6.26s/it]</span></div>



![png](img/nbs/output_9_1.png)


<br>

### Summary Statistics

We'll start by calculating the average reflectance for a single month to check that no dodgy regions jump out. Interestly we can see mountainous regions such as the Alps jump out due to the high reflectance of snow.

```python
%%time # takes ca.18 mins

da_HRV_mean = (ds
               ['stacked_eumetsat_data']
               .sel(variable='HRV', time='2020-03')
               .mean(dim='time')
              )

# Plotting
fig = plt.figure(dpi=250, figsize=(10, 10))
ax = plt.axes(projection=ccrs.TransverseMercator())

da_HRV_mean.T.plot.imshow(ax=ax, cmap='magma', vmin=-200, vmax=400)

ax.coastlines(resolution='50m', alpha=0.8, color='white')
```

    <ipython-input-16-455a547b74f1>:2: UserWarning: The default value for the *approx* keyword argument to TransverseMercator will change from True to False after 0.18.
      ax = plt.axes(projection=ccrs.TransverseMercator())
    




    <cartopy.mpl.feature_artist.FeatureArtist at 0x20d83f79fd0>




![png](img/nbs/output_11_2.png)


<br>

We'll also look at how the average reflectance changes with time of day

```python
%%time
# if this fails take avg of x and y, then convert to df and process with pandas
da_HRV_hourly_mean = (ds
                      ['stacked_eumetsat_data']
                      .sel(variable='HRV', time='2020-03')
                      .groupby('time.dt.hour')
                      .mean(dim=['x', 'y'])
                      .compute()
                     )

da_HRV_hourly_mean.plot()
```

<br>

We'll also get the minimum and maximum values present for each variable

```python
#exports
def get_var_min_maxs(ds):
    mins = ds['stacked_eumetsat_data'].sel(time='2020-03').min(['time', 'x', 'y']).compute()
    maxs = ds['stacked_eumetsat_data'].sel(time='2020-03').max(['time', 'x', 'y']).compute()
    
    return mins, maxs
```

```python
mins, maxs = get_var_min_maxs(ds)

mins, maxs
```

    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\xarray\core\indexing.py:1369: PerformanceWarning: Slicing is producing a large chunk. To accept the large
    chunk and silence this warning, set the option
        >>> with dask.config.set(**{'array.slicing.split_large_chunks': False}):
        ...     array[indexer]
    
    To avoid creating the large chunks, set the option
        >>> with dask.config.set(**{'array.slicing.split_large_chunks': True}):
        ...     array[indexer]
      return self.array[key]
    

<br>

### Offline Validation

We'll now do some quick data quality checks, including checking for duplicates and any null values. We'll start with the duplicates.

```python
#exports
def check_for_duplicates(ds):
    ds_dts = pd.to_datetime(ds.time.values)
    num_dupes = ds_dts.duplicated().sum()
    
    assert num_dupes == 0, f'There are {num_dupes} duplicate indexes in the database'
    
    return 
```

```python
check_for_duplicates(ds)
```

<br>

Then check for any nulls.

```python
#exports
get_null_count = lambda ds: (ds==-1).sum()
```

```python
%%time

get_null_count(ds)
```
