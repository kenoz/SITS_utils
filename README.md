# SITS Python Package

SITS is a Python library for dealing with satellite images time-series.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install [SITS](https://pypi.org/project/SITS/).

```bash
pip install SITS
```

## Usage

Here is a basic Python script example. For more details, read the documentation [here](https://sits.readthedocs.io/en/latest/index.html).

```python
import sits

# loads csv table with geographic coordinates into GeoDataFrame object
csv_file = 'my_file.csv'

# instantiates a SITS.Csv2gdf object
sits_df = sits.Csv2gdf(csv_file, 'lon', 'lat', 4326)

# converts coordinates of sits_df into EPSG:3035 
sits_df.set_gdf(3035)

# calculates buffer with a radius of 100 m for each feature.
sits_df.set_buffer('gdf', 100)

# calculates the boundiug box for each buffered feature.
sits_df.set_bbox('buffer')

# exports geometries as a GIS vector file
sits_df.to_vector('bbox', 'output/my_file_bbox.geojson', driver='GeoJSON')

# gets Sentinel-2 time-series from STAC catalog

# requests STAC catalog for each geometries of sits_df.bbox
for index, row in sits_df.bbox.iterrows():
    gid = sits_df.bbox.loc[index, 'gid']
    
    row_geom = sits_df.bbox.loc[index, 'geometry']
    row_geom_4326 = sits_df.bbox.to_crs(4326).loc[index, 'geometry']
    
    aoi_bounds = list(row_geom.bounds)
    aoi_bounds_4326 = list(row_geom_4326.bounds)

    # opens access to a STAC provider (by default Microsoft Planetary)
    imgs = sits.StacAttack()
    # searches items based on bbox coordinates and time interval criteria
    imgs.searchItems(aoi_bounds_4326, 
                     date_start=datetime(2016, 1, 1), 
                     date_end=datetime(2019, 12, 31))
    
    # extracts Sentinel-2 metadata and writes in csv file.
    imgs.items_prop["station_id"] = gid
    imgs.items_prop.to_csv(f'output/id_{gid}_s2_metadata.csv')
    
    # loads time-series images in EPSG:3035
    imgs.loadImgs(aoi_bounds, crs_out=3035)
    
    # exports time-series into csv file and netCDF file
    imgs.to_csv(out_dir, gid)
    imgs.to_nc(out_dir, gid, 'image')
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[GNU GPL v.3.0](LICENSE)