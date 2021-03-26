# Reprojecting



```
from satip import reproj

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import os
```

<br>

### User Inputs

We have to specify the directory where the data native filepaths are located

```
data_dir = '../data/raw'
```

<br>

### Loading the Scene

We'll then load the file using the reproj library

```
native_fps = sorted([f'{data_dir}/{f}' for f in os.listdir(data_dir) if '.nat' in f])
native_fp = native_fps[0]

scene = reproj.load_scene(native_fp)
scene.load(['HRV'])
```

    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\pyproj\crs\crs.py:543: UserWarning: You will likely lose important projection information when converting to a PROJ string from another format. See: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems
      proj_string = self.to_proj4()
    

<br>

Next we'll visualise the data in the HRV layer. 

In this particular image it looks like we've caught a period where the satellite is slightly off-kilter. Fortunately the area definition we create accounts for periods when this occurs.

```
seviri = reproj.get_seviri_area_def(native_fp)
seviri_crs = seviri.to_cartopy_crs()

# Plotting
fig = plt.figure(dpi=250, figsize=(10, 10))
ax = plt.axes(projection=seviri_crs)

scene['HRV'].plot.imshow(ax=ax, add_colorbar=False, cmap='magma', vmin=0, vmax=50)

ax.set_title('')
ax.coastlines(resolution='50m', alpha=0.8, color='white')
```

    C:\Users\Ayrto\anaconda3\envs\satip_dev\lib\site-packages\pyproj\crs\crs.py:543: UserWarning: You will likely lose important projection information when converting to a PROJ string from another format. See: https://proj.org/faq.html#what-is-the-best-format-for-describing-coordinate-reference-systems
      proj_string = self.to_proj4()
    




    <cartopy.mpl.feature_artist.FeatureArtist at 0x28f1fdd6970>




![png](img/nbs/output_6_2.png)


<br>

### Reprojection

The main way to carry out a reprojection is with the `Reprojector` class

```
reprojector = reproj.Reprojector()

reprojector
```




    <satip.reproj.Reprojector at 0x28f14995100>



<br>

From which the `reproject` method can be called, the default method that will be used is through `pyresample`

```
%%capture --no-stdout
%%time

ds_reproj = reprojector.reproject(native_fp)
```

    Wall time: 5.58 s
    

```
ds_reproj
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
Dimensions:                (variable: 12, x: 1870, y: 1831)
Coordinates:
  * y                      (y) float64 9.012e+06 9.008e+06 ... 1.692e+06
  * x                      (x) float64 -3.088e+06 -3.084e+06 ... 4.388e+06
  * variable               (variable) object &#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;
Data variables:
    stacked_eumetsat_data  (variable, y, x) float32 dask.array&lt;chunksize=(1, 1831, 1870), meta=np.ndarray&gt;</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.Dataset</div></div><ul class='xr-sections'><li class='xr-section-item'><input id='section-d0f17388-a23f-4ad8-8b7a-5f3dfefa656e' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-d0f17388-a23f-4ad8-8b7a-5f3dfefa656e' class='xr-section-summary'  title='Expand/collapse section'>Dimensions:</label><div class='xr-section-inline-details'><ul class='xr-dim-list'><li><span class='xr-has-index'>variable</span>: 12</li><li><span class='xr-has-index'>x</span>: 1870</li><li><span class='xr-has-index'>y</span>: 1831</li></ul></div><div class='xr-section-details'></div></li><li class='xr-section-item'><input id='section-2dfda3e3-7d65-430d-b977-d854b0fa22a4' class='xr-section-summary-in' type='checkbox'  checked><label for='section-2dfda3e3-7d65-430d-b977-d854b0fa22a4' class='xr-section-summary' >Coordinates: <span>(3)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>9.012e+06 9.008e+06 ... 1.692e+06</div><input id='attrs-d04751e0-1f16-4ca6-941f-7c591afa9722' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-d04751e0-1f16-4ca6-941f-7c591afa9722' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-15b10783-dfa3-41c1-bb7f-c07321467504' class='xr-var-data-in' type='checkbox'><label for='data-15b10783-dfa3-41c1-bb7f-c07321467504' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([9012000., 9008000., 9004000., ..., 1700000., 1696000., 1692000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>-3.088e+06 -3.084e+06 ... 4.388e+06</div><input id='attrs-2c2162eb-c8fd-4555-b75b-9c04716b06a0' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-2c2162eb-c8fd-4555-b75b-9c04716b06a0' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-c440ad62-46d4-4499-b4de-d84f700714f1' class='xr-var-data-in' type='checkbox'><label for='data-c440ad62-46d4-4499-b4de-d84f700714f1' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([-3088000., -3084000., -3080000., ...,  4380000.,  4384000.,  4388000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>variable</span></div><div class='xr-var-dims'>(variable)</div><div class='xr-var-dtype'>object</div><div class='xr-var-preview xr-preview'>&#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;</div><input id='attrs-1610498a-c846-4423-a723-1e639c47fb4c' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-1610498a-c846-4423-a723-1e639c47fb4c' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-35d66067-00b0-4e74-b91b-98b848feaacd' class='xr-var-data-in' type='checkbox'><label for='data-35d66067-00b0-4e74-b91b-98b848feaacd' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;HRV&#x27;, &#x27;IR_016&#x27;, &#x27;IR_039&#x27;, &#x27;IR_087&#x27;, &#x27;IR_097&#x27;, &#x27;IR_108&#x27;, &#x27;IR_120&#x27;,
       &#x27;IR_134&#x27;, &#x27;VIS006&#x27;, &#x27;VIS008&#x27;, &#x27;WV_062&#x27;, &#x27;WV_073&#x27;], dtype=object)</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-a10bc681-7ec0-4b86-850f-1261e5000aa6' class='xr-section-summary-in' type='checkbox'  checked><label for='section-a10bc681-7ec0-4b86-850f-1261e5000aa6' class='xr-section-summary' >Data variables: <span>(1)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span>stacked_eumetsat_data</span></div><div class='xr-var-dims'>(variable, y, x)</div><div class='xr-var-dtype'>float32</div><div class='xr-var-preview xr-preview'>dask.array&lt;chunksize=(1, 1831, 1870), meta=np.ndarray&gt;</div><input id='attrs-b54101d8-dab6-49d5-b13a-f29fe42819d1' class='xr-var-attrs-in' type='checkbox' ><label for='attrs-b54101d8-dab6-49d5-b13a-f29fe42819d1' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-caa22b47-4afa-4b9f-ad9d-3d4095ea1af0' class='xr-var-data-in' type='checkbox'><label for='data-caa22b47-4afa-4b9f-ad9d-3d4095ea1af0' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'><dt><span>orbital_parameters :</span></dt><dd>{&#x27;projection_longitude&#x27;: 9.5, &#x27;projection_latitude&#x27;: 0.0, &#x27;projection_altitude&#x27;: 35785831.0}</dd><dt><span>sun_earth_distance_correction_applied :</span></dt><dd>True</dd><dt><span>sun_earth_distance_correction_factor :</span></dt><dd>0.9697642568677852</dd><dt><span>units :</span></dt><dd>%</dd><dt><span>wavelength :</span></dt><dd>0.7â€¯ÂµmÂ (0.5-0.9â€¯Âµm)</dd><dt><span>standard_name :</span></dt><dd>toa_bidirectional_reflectance</dd><dt><span>platform_name :</span></dt><dd>Meteosat-9</dd><dt><span>sensor :</span></dt><dd>seviri</dd><dt><span>start_time :</span></dt><dd>2020-12-08 09:00:08.206321</dd><dt><span>end_time :</span></dt><dd>2020-12-08 09:05:08.329479</dd><dt><span>area :</span></dt><dd>Area ID: geos_seviri_hrv
Description: SEVIRI high resolution channel area
Projection ID: seviri_hrv
Projection: {&#x27;a&#x27;: &#x27;6378169&#x27;, &#x27;h&#x27;: &#x27;35785831&#x27;, &#x27;lon_0&#x27;: &#x27;9.5&#x27;, &#x27;no_defs&#x27;: &#x27;None&#x27;, &#x27;proj&#x27;: &#x27;geos&#x27;, &#x27;rf&#x27;: &#x27;295.488065897014&#x27;, &#x27;type&#x27;: &#x27;crs&#x27;, &#x27;units&#x27;: &#x27;m&#x27;, &#x27;x_0&#x27;: &#x27;0&#x27;, &#x27;y_0&#x27;: &#x27;0&#x27;}
Number of columns: 5568
Number of rows: 4176
Area extent: (3164925.147, 5571248.3904, -2403822.9075, 1394687.3495)</dd><dt><span>name :</span></dt><dd>HRV</dd><dt><span>resolution :</span></dt><dd>1000.134348869</dd><dt><span>calibration :</span></dt><dd>reflectance</dd><dt><span>modifiers :</span></dt><dd>()</dd><dt><span>_satpy_id :</span></dt><dd>DataID(name=&#x27;HRV&#x27;, wavelength=WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), resolution=1000.134348869, calibration=&lt;calibration.reflectance&gt;, modifiers=())</dd><dt><span>ancillary_variables :</span></dt><dd>[]</dd></dl></div><div class='xr-var-data'><table>
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
</table></div></li></ul></div></li><li class='xr-section-item'><input id='section-c5d13cca-85bc-47c5-9be5-b861e086008f' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-c5d13cca-85bc-47c5-9be5-b861e086008f' class='xr-section-summary'  title='Expand/collapse section'>Attributes: <span>(0)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'></dl></div></li></ul></div></div>



<br>

It's also possible to use the functional api, e.g. for our task we could have used `full_scene_pyresample` to achieve the same results.

```
%%capture --no-stdout
%%time

ds_reproj = reproj.full_scene_pyresample(native_fp)
```

    Wall time: 4.98 s
    

```
ds_reproj
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
Dimensions:                (variable: 12, x: 1870, y: 1831)
Coordinates:
  * y                      (y) float64 9.012e+06 9.008e+06 ... 1.692e+06
  * x                      (x) float64 -3.088e+06 -3.084e+06 ... 4.388e+06
  * variable               (variable) object &#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;
Data variables:
    stacked_eumetsat_data  (variable, y, x) float32 dask.array&lt;chunksize=(1, 1831, 1870), meta=np.ndarray&gt;</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.Dataset</div></div><ul class='xr-sections'><li class='xr-section-item'><input id='section-240d1b06-ace1-44ec-a26e-7af78301e80f' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-240d1b06-ace1-44ec-a26e-7af78301e80f' class='xr-section-summary'  title='Expand/collapse section'>Dimensions:</label><div class='xr-section-inline-details'><ul class='xr-dim-list'><li><span class='xr-has-index'>variable</span>: 12</li><li><span class='xr-has-index'>x</span>: 1870</li><li><span class='xr-has-index'>y</span>: 1831</li></ul></div><div class='xr-section-details'></div></li><li class='xr-section-item'><input id='section-8715e63d-12ce-47c1-99d5-50b64e93be81' class='xr-section-summary-in' type='checkbox'  checked><label for='section-8715e63d-12ce-47c1-99d5-50b64e93be81' class='xr-section-summary' >Coordinates: <span>(3)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>9.012e+06 9.008e+06 ... 1.692e+06</div><input id='attrs-84eb7f5d-c2ae-4b8a-946f-8166ede4555a' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-84eb7f5d-c2ae-4b8a-946f-8166ede4555a' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-8de51138-4337-4de1-8973-dbeebbb60ca3' class='xr-var-data-in' type='checkbox'><label for='data-8de51138-4337-4de1-8973-dbeebbb60ca3' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([9012000., 9008000., 9004000., ..., 1700000., 1696000., 1692000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>-3.088e+06 -3.084e+06 ... 4.388e+06</div><input id='attrs-fc68685e-98f7-492b-89d5-aa9f5921e156' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-fc68685e-98f7-492b-89d5-aa9f5921e156' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-d170113e-32fb-4b05-a4e9-36b9a38630b6' class='xr-var-data-in' type='checkbox'><label for='data-d170113e-32fb-4b05-a4e9-36b9a38630b6' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([-3088000., -3084000., -3080000., ...,  4380000.,  4384000.,  4388000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>variable</span></div><div class='xr-var-dims'>(variable)</div><div class='xr-var-dtype'>object</div><div class='xr-var-preview xr-preview'>&#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;</div><input id='attrs-7726a2ea-bfbb-4cdc-b4fe-e18a528fadb1' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-7726a2ea-bfbb-4cdc-b4fe-e18a528fadb1' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-448bd8be-064a-4cdd-bd95-d4e8581c3718' class='xr-var-data-in' type='checkbox'><label for='data-448bd8be-064a-4cdd-bd95-d4e8581c3718' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;HRV&#x27;, &#x27;IR_016&#x27;, &#x27;IR_039&#x27;, &#x27;IR_087&#x27;, &#x27;IR_097&#x27;, &#x27;IR_108&#x27;, &#x27;IR_120&#x27;,
       &#x27;IR_134&#x27;, &#x27;VIS006&#x27;, &#x27;VIS008&#x27;, &#x27;WV_062&#x27;, &#x27;WV_073&#x27;], dtype=object)</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-ac9c38ad-05e9-4930-9d7d-a9f8b0d73381' class='xr-section-summary-in' type='checkbox'  checked><label for='section-ac9c38ad-05e9-4930-9d7d-a9f8b0d73381' class='xr-section-summary' >Data variables: <span>(1)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span>stacked_eumetsat_data</span></div><div class='xr-var-dims'>(variable, y, x)</div><div class='xr-var-dtype'>float32</div><div class='xr-var-preview xr-preview'>dask.array&lt;chunksize=(1, 1831, 1870), meta=np.ndarray&gt;</div><input id='attrs-9297e3ac-760a-44d1-a978-fa3132a4821f' class='xr-var-attrs-in' type='checkbox' ><label for='attrs-9297e3ac-760a-44d1-a978-fa3132a4821f' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-a4d631ba-0203-4e76-ad0a-6c215a90a56b' class='xr-var-data-in' type='checkbox'><label for='data-a4d631ba-0203-4e76-ad0a-6c215a90a56b' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'><dt><span>orbital_parameters :</span></dt><dd>{&#x27;projection_longitude&#x27;: 9.5, &#x27;projection_latitude&#x27;: 0.0, &#x27;projection_altitude&#x27;: 35785831.0}</dd><dt><span>sun_earth_distance_correction_applied :</span></dt><dd>True</dd><dt><span>sun_earth_distance_correction_factor :</span></dt><dd>0.9697642568677852</dd><dt><span>units :</span></dt><dd>%</dd><dt><span>wavelength :</span></dt><dd>0.7â€¯ÂµmÂ (0.5-0.9â€¯Âµm)</dd><dt><span>standard_name :</span></dt><dd>toa_bidirectional_reflectance</dd><dt><span>platform_name :</span></dt><dd>Meteosat-9</dd><dt><span>sensor :</span></dt><dd>seviri</dd><dt><span>start_time :</span></dt><dd>2020-12-08 09:00:08.206321</dd><dt><span>end_time :</span></dt><dd>2020-12-08 09:05:08.329479</dd><dt><span>area :</span></dt><dd>Area ID: geos_seviri_hrv
Description: SEVIRI high resolution channel area
Projection ID: seviri_hrv
Projection: {&#x27;a&#x27;: &#x27;6378169&#x27;, &#x27;h&#x27;: &#x27;35785831&#x27;, &#x27;lon_0&#x27;: &#x27;9.5&#x27;, &#x27;no_defs&#x27;: &#x27;None&#x27;, &#x27;proj&#x27;: &#x27;geos&#x27;, &#x27;rf&#x27;: &#x27;295.488065897014&#x27;, &#x27;type&#x27;: &#x27;crs&#x27;, &#x27;units&#x27;: &#x27;m&#x27;, &#x27;x_0&#x27;: &#x27;0&#x27;, &#x27;y_0&#x27;: &#x27;0&#x27;}
Number of columns: 5568
Number of rows: 4176
Area extent: (3164925.147, 5571248.3904, -2403822.9075, 1394687.3495)</dd><dt><span>name :</span></dt><dd>HRV</dd><dt><span>resolution :</span></dt><dd>1000.134348869</dd><dt><span>calibration :</span></dt><dd>reflectance</dd><dt><span>modifiers :</span></dt><dd>()</dd><dt><span>_satpy_id :</span></dt><dd>DataID(name=&#x27;HRV&#x27;, wavelength=WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), resolution=1000.134348869, calibration=&lt;calibration.reflectance&gt;, modifiers=())</dd><dt><span>ancillary_variables :</span></dt><dd>[]</dd></dl></div><div class='xr-var-data'><table>
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
</table></div></li></ul></div></li><li class='xr-section-item'><input id='section-1241ca37-4cea-4e9d-aaea-8b6f788f571e' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-1241ca37-4cea-4e9d-aaea-8b6f788f571e' class='xr-section-summary'  title='Expand/collapse section'>Attributes: <span>(0)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'></dl></div></li></ul></div></div>



<br>

Alongside `pyresample` its also possible to use `pyinterp` which can be faster when the dataset has fewer layers. When using `pyinterp` we have to provide the coordinates of the new grid as well as the coordinates that grid has in the original CRS.

```
%%capture --no-stdout
%%time

new_coords_fp = f'../data/intermediate/reproj_coords_TM_4km.csv'
new_grid_fp = '../data/intermediate/new_grid_4km_TM.json'

reprojector = reproj.Reprojector(new_coords_fp, new_grid_fp)
ds_reproj = reprojector.reproject(native_fp, reproj_library='pyinterp')
```

    Wall time: 16.5 s
    

```
ds_reproj
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
Dimensions:                (variable: 12, x: 1870, y: 1831)
Coordinates:
  * x                      (x) float64 4.388e+06 4.384e+06 ... -3.088e+06
  * y                      (y) float64 1.692e+06 1.696e+06 ... 9.012e+06
  * variable               (variable) object &#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;
Data variables:
    stacked_eumetsat_data  (variable, y, x) float64 nan nan nan ... nan nan nan</pre><div class='xr-wrap' hidden><div class='xr-header'><div class='xr-obj-type'>xarray.Dataset</div></div><ul class='xr-sections'><li class='xr-section-item'><input id='section-f4a382c8-1a0d-421c-b1aa-d821864e0e1e' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-f4a382c8-1a0d-421c-b1aa-d821864e0e1e' class='xr-section-summary'  title='Expand/collapse section'>Dimensions:</label><div class='xr-section-inline-details'><ul class='xr-dim-list'><li><span class='xr-has-index'>variable</span>: 12</li><li><span class='xr-has-index'>x</span>: 1870</li><li><span class='xr-has-index'>y</span>: 1831</li></ul></div><div class='xr-section-details'></div></li><li class='xr-section-item'><input id='section-72d7376c-1648-4d3a-8a11-e7cf10db617e' class='xr-section-summary-in' type='checkbox'  checked><label for='section-72d7376c-1648-4d3a-8a11-e7cf10db617e' class='xr-section-summary' >Coordinates: <span>(3)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>x</span></div><div class='xr-var-dims'>(x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>4.388e+06 4.384e+06 ... -3.088e+06</div><input id='attrs-e21440db-2a18-48dd-af12-2c3770bd9985' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-e21440db-2a18-48dd-af12-2c3770bd9985' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-eac910d6-d7ef-4b92-aecb-a0b3aa3b7262' class='xr-var-data-in' type='checkbox'><label for='data-eac910d6-d7ef-4b92-aecb-a0b3aa3b7262' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([ 4388000.,  4384000.,  4380000., ..., -3080000., -3084000., -3088000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>y</span></div><div class='xr-var-dims'>(y)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>1.692e+06 1.696e+06 ... 9.012e+06</div><input id='attrs-91ef2ca0-3767-4dba-8461-d6f00fe357a2' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-91ef2ca0-3767-4dba-8461-d6f00fe357a2' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-5dadbc0d-e7c0-4dcb-bb08-cc1739a4eff7' class='xr-var-data-in' type='checkbox'><label for='data-5dadbc0d-e7c0-4dcb-bb08-cc1739a4eff7' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([1692000., 1696000., 1700000., ..., 9004000., 9008000., 9012000.])</pre></div></li><li class='xr-var-item'><div class='xr-var-name'><span class='xr-has-index'>variable</span></div><div class='xr-var-dims'>(variable)</div><div class='xr-var-dtype'>object</div><div class='xr-var-preview xr-preview'>&#x27;HRV&#x27; &#x27;IR_016&#x27; ... &#x27;WV_073&#x27;</div><input id='attrs-3df55702-e40a-48d8-af2a-9344ce3799f8' class='xr-var-attrs-in' type='checkbox' disabled><label for='attrs-3df55702-e40a-48d8-af2a-9344ce3799f8' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-2c8b310b-5861-4cc9-8d62-d5dc38a83a32' class='xr-var-data-in' type='checkbox'><label for='data-2c8b310b-5861-4cc9-8d62-d5dc38a83a32' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'></dl></div><div class='xr-var-data'><pre>array([&#x27;HRV&#x27;, &#x27;IR_016&#x27;, &#x27;IR_039&#x27;, &#x27;IR_087&#x27;, &#x27;IR_097&#x27;, &#x27;IR_108&#x27;, &#x27;IR_120&#x27;,
       &#x27;IR_134&#x27;, &#x27;VIS006&#x27;, &#x27;VIS008&#x27;, &#x27;WV_062&#x27;, &#x27;WV_073&#x27;], dtype=object)</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-e16ffc79-eb0f-4a0e-8270-9fd44f2df1db' class='xr-section-summary-in' type='checkbox'  checked><label for='section-e16ffc79-eb0f-4a0e-8270-9fd44f2df1db' class='xr-section-summary' >Data variables: <span>(1)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><ul class='xr-var-list'><li class='xr-var-item'><div class='xr-var-name'><span>stacked_eumetsat_data</span></div><div class='xr-var-dims'>(variable, y, x)</div><div class='xr-var-dtype'>float64</div><div class='xr-var-preview xr-preview'>nan nan nan nan ... nan nan nan nan</div><input id='attrs-e8f356e6-9d03-4701-af7e-198c8cb89255' class='xr-var-attrs-in' type='checkbox' ><label for='attrs-e8f356e6-9d03-4701-af7e-198c8cb89255' title='Show/Hide attributes'><svg class='icon xr-icon-file-text2'><use xlink:href='#icon-file-text2'></use></svg></label><input id='data-1727fdb6-b679-4555-b75c-ccad3f5149e8' class='xr-var-data-in' type='checkbox'><label for='data-1727fdb6-b679-4555-b75c-ccad3f5149e8' title='Show/Hide data repr'><svg class='icon xr-icon-database'><use xlink:href='#icon-database'></use></svg></label><div class='xr-var-attrs'><dl class='xr-attrs'><dt><span>orbital_parameters :</span></dt><dd>{&#x27;projection_longitude&#x27;: 9.5, &#x27;projection_latitude&#x27;: 0.0, &#x27;projection_altitude&#x27;: 35785831.0}</dd><dt><span>sun_earth_distance_correction_applied :</span></dt><dd>True</dd><dt><span>sun_earth_distance_correction_factor :</span></dt><dd>0.9697642568677852</dd><dt><span>units :</span></dt><dd>%</dd><dt><span>wavelength :</span></dt><dd>0.7â€¯ÂµmÂ (0.5-0.9â€¯Âµm)</dd><dt><span>standard_name :</span></dt><dd>toa_bidirectional_reflectance</dd><dt><span>platform_name :</span></dt><dd>Meteosat-9</dd><dt><span>sensor :</span></dt><dd>seviri</dd><dt><span>start_time :</span></dt><dd>2020-12-08 09:00:08.206321</dd><dt><span>end_time :</span></dt><dd>2020-12-08 09:05:08.329479</dd><dt><span>area :</span></dt><dd>Area ID: geos_seviri_hrv
Description: SEVIRI high resolution channel area
Projection ID: seviri_hrv
Projection: {&#x27;a&#x27;: &#x27;6378169&#x27;, &#x27;h&#x27;: &#x27;35785831&#x27;, &#x27;lon_0&#x27;: &#x27;9.5&#x27;, &#x27;no_defs&#x27;: &#x27;None&#x27;, &#x27;proj&#x27;: &#x27;geos&#x27;, &#x27;rf&#x27;: &#x27;295.488065897014&#x27;, &#x27;type&#x27;: &#x27;crs&#x27;, &#x27;units&#x27;: &#x27;m&#x27;, &#x27;x_0&#x27;: &#x27;0&#x27;, &#x27;y_0&#x27;: &#x27;0&#x27;}
Number of columns: 5568
Number of rows: 4176
Area extent: (3164925.147, 5571248.3904, -2403822.9075, 1394687.3495)</dd><dt><span>name :</span></dt><dd>HRV</dd><dt><span>resolution :</span></dt><dd>1000.134348869</dd><dt><span>calibration :</span></dt><dd>reflectance</dd><dt><span>modifiers :</span></dt><dd>()</dd><dt><span>_satpy_id :</span></dt><dd>DataID(name=&#x27;HRV&#x27;, wavelength=WavelengthRange(min=0.5, central=0.7, max=0.9, unit=&#x27;Âµm&#x27;), resolution=1000.134348869, calibration=&lt;calibration.reflectance&gt;, modifiers=())</dd><dt><span>ancillary_variables :</span></dt><dd>[]</dd></dl></div><div class='xr-var-data'><pre>array([[[nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        ...,
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan]],

       [[nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        ...,
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan]],

       [[nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        ...,
...
        ...,
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan]],

       [[nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        ...,
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan]],

       [[nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        ...,
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan]]])</pre></div></li></ul></div></li><li class='xr-section-item'><input id='section-f6f6c8cf-463d-4e32-9d5c-bd6c3e3531c8' class='xr-section-summary-in' type='checkbox' disabled ><label for='section-f6f6c8cf-463d-4e32-9d5c-bd6c3e3531c8' class='xr-section-summary'  title='Expand/collapse section'>Attributes: <span>(0)</span></label><div class='xr-section-inline-details'></div><div class='xr-section-details'><dl class='xr-attrs'></dl></div></li></ul></div></div>


