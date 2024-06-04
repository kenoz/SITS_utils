import os
import pandas as pd
import geopandas as gpd
import xarray as xr
from shapely.geometry import box
from rasterio.crs import CRS
# STAC API
from pystac_client import Client
import planetary_computer as pc
# ODC tools
import odc
from odc.geo.geobox import GeoBox
from odc.stac import configure_rio, stac_load

class Csv2gdf:

    def __init__(self, csv_file, x_name, y_name, crs_in, id_name='no_id'):
        """Init class object

        csv_file: path to csv file
        """
        self.crs_in = crs_in
        self.table = pd.read_csv(csv_file, encoding= 'unicode_escape')
        self.table = self.table.rename(columns={x_name: 'coord_X',
                                                y_name: 'coord_Y',
                                                id_name: 'gid'})

    def set_gdf(self, crs_out, outfile=None):
        self.gdf = gpd.GeoDataFrame(self.table,
                                    geometry=gpd.points_from_xy(self.table.coord_X,
                                                                self.table.coord_Y)
                                   )
        self.gdf = self.gdf.set_crs(self.crs_in, allow_override=True)
        self.gdf = self.gdf.to_crs(crs_out)

    def set_buffer(self, df_attr, radius, outfile=None):
        df = getattr(self, df_attr)
        self.buffer = df.copy()
        self.buffer['geometry'] = self.buffer.geometry.buffer(radius)

    def set_bbox(self, df_attr, outfile=None):
        df = getattr(self, df_attr)
        self.bbox = df.copy()
        self.bbox['geometry'] = self.bbox.apply(self.__create_bounding_box, axis=1)

    def to_vector(self, df_attr, outfile=None, driver="GeoJSON"):
        df = getattr(self, df_attr)
        df.to_file(outfile, driver=driver, encoding='utf-8')

    def del_rows(self, col_name, rows_values):
        """
        rows_values: list
        """
        size_before = len(self.table)
        del_rows = {col_name:rows_values}
        for col in del_rows:
            for row in del_rows[col]:
                self.table.drop(self.table[self.table[col] == row].index, 
                                inplace = True)
        size_after = len(self.table)
        print(f'rows length before:{size_before}\nrows length after:{size_after}')

    def __create_bounding_box(self, row):
        xmin, ymin, xmax, ymax = row.geometry.bounds
        return box(xmin, ymin, xmax, ymax)

class StacAttack:

    def __init__(self, provider='mpc', collection='sentinel-2-l2a'):
        self.prov_stac = {'mpc':{'stac': 'https://planetarycomputer.microsoft.com/api/stac/v1',
                                 'coll': collection,
                                 'modifier': pc.sign_inplace,
                                 'patch_url': pc.sign},
                          'aws':{'stac': 'https://earth-search.aws.element84.com/v1/',
                                 'coll': collection,
                                 'modifier': None,
                                 'patch_url': None}
                         }
        self.stac = self.prov_stac[provider]
        self.catalog = Client.open(self.stac['stac'], modifier=self.stac['modifier'])

    def searchItems(self, bbox_latlon, date_start='2023-01', date_end='2023-12', **kwargs):
        self.startdate = date_start
        self.enddate = date_end
        time_range = "{}/{}".format(self.startdate, self.enddate)
        query = self.catalog.search(collections=[self.stac['coll']],
                                    datetime=time_range,
                                    bbox=bbox_latlon,
                                    **kwargs
                                   )
        self.items = list(query.items())

    def loadPatches(self, bbox, resolution, dimx, dimy,
                    bands=['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 
                           'B8A', 'B11', 'B12', 'SCL'],
                    crs_out=3035, chunks_size=612, dtype="uint16", nodata=0):

        shape = (dimx, dimy)

        self.def_geobox(bbox, crs_out, resolution, shape)

        self.p_array = stac_load(self.items,
                               bands=bands,
                               groupby="solar_day",
                               chunks={"x": chunks_size, "y": chunks_size},
                               patch_url=self.stac['patch_url'],
                               dtype=dtype,
                               nodata=nodata,
                               geobox=self.geobox
                     )

    def loadImgs(self, bbox, resolution=10,
                 bands=['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 
                        'B8A', 'B11', 'B12', 'SCL'],
                 crs_out=3035, chunks_size=612, dtype="uint16", nodata=0
                 ):

        self.def_geobox(bbox, crs_out, resolution)

        self.i_array = stac_load(self.items,
                               bands=bands,
                               groupby="solar_day",
                               chunks={"x": chunks_size, "y": chunks_size},
                               patch_url=self.stac['patch_url'],
                               dtype=dtype,
                               nodata=nodata,
                               geobox=self.geobox
                     )

    def __choose_array(self, array_type):
        if array_type == 'image':
            e_array = self.i_array
        elif array_type == 'patch':
            e_array = self.p_array
        return e_array

    def to_df(self, array_type):
        e_array = self.__choose_array(array_type)
        array_trans = e_array.transpose('time', 'y', 'x')
        df = array_trans.to_dataframe()
        return df

    def to_csv(self, df, outdir, gid=None):
        df = df.reset_index()
        df['ID'] = df.index
        if gid is not None:
            df.to_csv(os.path.join(outdir, f'id_{gid}_{array_type}.csv'))
        else:
            df.to_csv(os.path.join(outdir, f'id_none_{array_type}.csv'))

    def old_to_csv(self, array_type, gid, outdir):
        """deprecated"""
        self.df = self.df.reset_index()
        self.df['ID'] = self.df.index
        self.df.insert(0, "station", gid)
        self.df['date'] = pd.to_datetime(self.df['time']).dt.date
        self.df.to_csv(os.path.join(outdir, f'station_{gid}_{array_type}.csv'))

    def to_nc(self, array_type, gid, outdir):
        e_array = self.__choose_array(array_type)
        e_array.to_netcdf(f"{outdir}/S2_fid-{gid}_{array_type}_{self.startdate}-{self.enddate}.nc")

    def def_geobox(self, bbox, crs_out, resolution, shape=None):

        crs = CRS.from_epsg(crs_out)
        if shape is not None:
            # size in pixels of input bbox
            size_x = round((bbox[2] - bbox[0]) / resolution)
            size_y = round((bbox[3] - bbox[1]) / resolution)
            print(size_x, size_y)
            # shift size to reach the shape
            shift_x = round((shape[0] - size_x) / 2)
            shift_y = round((shape[1] - size_y) / 2)
            # coordinates of the shaped bbox
            min_x = resolution * (round(bbox[0]/resolution) - shift_x)
            min_y = resolution * (round(bbox[1]/resolution) - shift_y)
            max_x = min_x + shape[0] * resolution
            max_y = min_y + shape[1] * resolution

            self.newbbox = [min_x, min_y, max_x, max_y]
        else:
            self.newbbox = bbox

        self.geobox = GeoBox.from_bbox(odc.geo.geom.BoundingBox(*self.newbbox),
                                       crs=crs,
                                       resolution=resolution)