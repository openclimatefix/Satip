import shutil
import glob

zarr_paths = list(glob.glob("/mnt/storage_ssd/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v2/eumetsat_zarr_*"))
for zarr_path in zarr_paths:
    dataset: xr.Dataset = xr.open_dataset(zarr_path, engine = 'zarr')
    print(dataset)
    if dataset.coords["x"] == osgb_x:
        continue
    dataset = dataset.assign_coords(x=osgb_x,y=osgb_y)
    print(dataset)
    dataset.to_zarr(zarr_path, mode='a', compute = True)

scene = Scene(filenames={"seviri_l1b_native": [filename]})
scene.load(
    [
        "HRV",
        ]
    )

scene = scene.crop(ll_bbox=GEOGRAPHIC_BOUNDS['UK'])
# Lat and Lon are the same for all the channels now
lon, lat = scene['HRV'].attrs["area"].get_lonlats()
osgb_x, osgb_y = lat_lon_to_osgb(lat, lon)
osgb_y = osgb_y[:,0]
osgb_x = osgb_x[0,:]
zarr_paths = list(glob.glob("/mnt/storage_ssd/data/ocf/solar_pv_nowcasting/nowcasting_dataset_pipeline/satellite/EUMETSAT/SEVIRI_RSS/zarr/v2/hrv_eumetsat_zarr_*"))
for zarr_path in zarr_paths:
    dataset: xr.Dataset = xr.open_dataset(zarr_path, engine = 'zarr')
    print(dataset)
    dataset = dataset.assign_coords(x=osgb_x,y=osgb_y)
    print(dataset)
    dataset.to_zarr(zarr_path, mode='a', compute = True)