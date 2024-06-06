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
# Geospatial librairies
import rasterio
from rasterio.features import rasterize


class Csv2gdf:
    """
    This class aims to load csv tables with geographic coordinates into GeoDataFrame object.

    Attributes:
        crs_in (int): CRS of coordinates decsribed in the csv table.
        table (DataFrame): DataFrame.

    Methods:
        set_gdf(self, crs_out, outfile=None): import csv file as `geopandas.GeoDataFrame`.
        set_buffer(self, df_attr, radius, outfile=None): return buffer geometries for each point.
        set_bbox(self, df_attr, outfile=None): return bounding boxes for each geometry.
        to_vector(self, df_attr, outfile=None, driver="GeoJSON"): write GeoDataFrame as vector file.
        del_rows(self, col_name, rows_values): remove GeoDataFrame rows.
        __create_bounding_box(self, row): return bounding box coordinates.

    Example:
        >>> geotable = Csv2gdf(csv_file, 'longitude', 'latitude', 3035)
        >>> geotable.set_gdf(3035, 'output/table.geojson')
    """

    def __init__(self, csv_file, x_name, y_name, crs_in, id_name='no_id'):
        """
        Initialize the attributes of Csv2gdf.

        Args:
            csv_file (str): csv filepath.
            x_name (str): name of the field describing X coordinates.
            y_name (str): name of the field describing Y coordinates.
            crs_in (int): CRS of coordinates described in the CSV table.
            id_name (str, optional): name of the ID field. Defaults to "no_id".
        """
        self.crs_in = crs_in
        self.table = pd.read_csv(csv_file, encoding= 'unicode_escape')
        self.table = self.table.rename(columns={x_name: 'coord_X',
                                                y_name: 'coord_Y',
                                                id_name: 'gid'})

    def set_gdf(self, crs_out, outfile=None):
        """
        Convert the `Csv2gdf` attribute `table` (DataFrame) into GeoDataFrame object.

        Args:
            crs_out (int): output CRS of GeoDataFrame.
            outfile (str, optional): Defaults to `None`.

        Returns:
            Csv2gdf.gdf (GeoDataFrame): GeoDataFrame object.
        """
        self.gdf = gpd.GeoDataFrame(self.table,
                                    geometry=gpd.points_from_xy(self.table.coord_X,
                                                                self.table.coord_Y)
                                   )
        self.gdf = self.gdf.set_crs(self.crs_in, allow_override=True)
        self.gdf = self.gdf.to_crs(crs_out)

    def set_buffer(self, df_attr, radius, outfile=None):
        """
        Calculate buffer geometries of a Csv2gdf GeoDataFrame object.

        Args:
            df_attr (str): GeoDataFrame attribute of class `Csv2gdf`.
                Can be one of the following: 'gdf', 'buffer', 'bbox'.
            radius (float): buffer distance in CRS unit.
            outfile (str, optional): ouput filepath. Defaults to `None`.

        Returns:
            Csv2gdf.buffer (GeoDataFrame): GeoDataFrame object.
        """
        df = getattr(self, df_attr)
        self.buffer = df.copy()
        self.buffer['geometry'] = self.buffer.geometry.buffer(radius)

    def set_bbox(self, df_attr, outfile=None):
        """
        Calculate the bounding box of a Csv2gdf GeoDataFrame object.

        Args:
            df_attr (str): GeoDataFrame attribute of class `Csv2gdf`.
                Can be one of the following: 'gdf', 'buffer', 'bbox'.
            outfile (str, optional): ouput filepath. Defaults to `None`.

        Returns:
            Csv2gdf.bbox (GeoDataFrame): GeoDataFrame object.
        """
        df = getattr(self, df_attr)
        self.bbox = df.copy()
        self.bbox['geometry'] = self.bbox.apply(self.__create_bounding_box, axis=1)

    def to_vector(self, df_attr, outfile=None, driver="GeoJSON"):
        """
        Write a Csv2gdf GeoDataFrame object as a vector file.

        Args:
            df_attr (str): GeoDataFrame attribute of class `Csv2gdf`.
                Can be one of the following: 'gdf', 'buffer', 'bbox'.
            outfile (str, optional): . Defaults to `None`.
            driver (str, optional): . Defaults to "GeoJSON".
        """
        df = getattr(self, df_attr)
        df.to_file(outfile, driver=driver, encoding='utf-8')

    def del_rows(self, col_name, rows_values):
        """
        Drop rows from Csv2gdf.table according to a column's values.

        Args:
            col_name (str): column name.
            rows_values (list): list of values.
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
        """
        Create the bounding box of a feature's geometry.

        Args:
            row (GeoSeries): GeoDataFrame's row.

        Returns:
            shapely.geometry.box
        """
        xmin, ymin, xmax, ymax = row.geometry.bounds
        return box(xmin, ymin, xmax, ymax)


class StacAttack:
    """
    This class aims to request time-series on STAC catalog and store it as image or csv files.

    Attributes:
        prov_stac (dict): STAC providers.
        stac (dict): STAC providers' parameters.
        catalog (pystac.Catalog): Access to STAC catalog
        bands (list): list of satellite collection's bands to request.
        stac_conf (dict): parameters for building datacube (xArray) from STAC items.

    Methods:
        __items_to_array(self):
        __choose_array(self, array_type):
        __to_df(self, array_type):
        searchItems(self, bbox_latlon, date_start='2023-01', date_end='2023-12', **kwargs):
        loadPatches(self, bbox, dimx=5, dimy=5, resolution=10, crs_out=3035):
        loadImgs(self, bbox, resolution=10, crs_out=3035):
        to_csv(self, outdir, gid=None, array_type='image'):
        to_nc(self, array_type, gid, outdir):
        def_geobox(self, bbox, crs_out, resolution, shape=None):

    Example:
        >>> XXXX geotable = Csv2gdf(csv_file, 'longitude', 'latitude', 3035)
        >>> XXXX geotable.set_gdf(3035, 'output/table.geojson')
    """

    def __init__(self, provider='mpc',
                       collection='sentinel-2-l2a',
                       bands=['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'SCL']
                ):
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
        self.bands = bands
        self.stac_conf = {'chunks_size':612, 'dtype':"uint16", 'nodata':0}

    def __items_to_array(self):
        arr = stac_load(self.items,
                        bands=self.bands,
                        groupby="solar_day",
                        chunks={"x": self.stac_conf['chunks_size'], 
                                "y": self.stac_conf['chunks_size']},
                        patch_url=self.stac['patch_url'],
                        dtype=self.stac_conf['dtype'],
                        nodata=self.stac_conf['nodata'],
                        geobox=self.geobox
                        )
        return arr

    def __choose_array(self, array_type):
        if array_type == 'image':
            e_array = self.i_array
        elif array_type == 'patch':
            e_array = self.p_array
        return e_array

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

    def loadPatches(self, bbox, dimx=5, dimy=5, resolution=10, crs_out=3035):

        shape = (dimx, dimy)
        self.def_geobox(bbox, crs_out, resolution, shape)

        self.patch = self.__items_to_array()

    def loadImgs(self, bbox, resolution=10, crs_out=3035):

        self.def_geobox(bbox, crs_out, resolution)

        self.image = self.__items_to_array()

    def __to_df(self, array_type):
        #e_array = self.__choose_array(array_type)
        e_array = getattr(self, array_type)
        array_trans = e_array.transpose('time', 'y', 'x')
        df = array_trans.to_dataframe()
        return df

    def to_csv(self, outdir, gid=None, array_type='image'):
        df = self.__to_df(array_type)
        df = df.reset_index()
        df['ID'] = df.index
        if gid is not None:
            df.to_csv(os.path.join(outdir, f'id_{gid}_{array_type}.csv'))
        else:
            df.to_csv(os.path.join(outdir, f'id_none_{array_type}.csv'))

    def to_nc(self, array_type, gid, outdir):
        #e_array = self.__choose_array(array_type)
        e_array = getattr(self, array_type)
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

    def old_to_csv(self, array_type, gid, outdir):
        """deprecated"""
        self.df = self.df.reset_index()
        self.df['ID'] = self.df.index
        self.df.insert(0, "station", gid)
        self.df['date'] = pd.to_datetime(self.df['time']).dt.date
        self.df.to_csv(os.path.join(outdir, f'station_{gid}_{array_type}.csv'))


class Labels:
    def __init__(self, geolayer):
        if isinstance(geolayer, pd.core.frame.DataFrame):
            self.gdf = geolayer.copy()
        else:
            self.gdf = gpd.read_file(geolayer)
        #self.geom = self.gdf.geometry

    def to_raster(self, id_field, geobox, filename, outdir, crs='EPSG:3035', driver="GTiff"):
        shapes = ((geom, value) for geom, value in zip(self.gdf.geometry, self.gdf[id_field]))
        rasterized = rasterize(#[(self.geom.iloc[0], 255)],
                               shapes, 
                               out_shape=(geobox.height, geobox.width),
                               transform=geobox.transform,
                               fill=0,
                               all_touched=False,
                               dtype='uint8')

        # Write the rasterized feature to a new raster file
        with rasterio.open(os.path.join(outdir, filename), 'w', driver=driver, crs=crs,
                           transform=geobox.transform, dtype=rasterio.uint8, count=1, 
                           width=geobox.width, height=geobox.height) as dst:
            dst.write(rasterized, 1)
