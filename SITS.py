import os
import pandas as pd
import numpy as np
from datetime import datetime
# STAC API
from pystac_client import Client
import planetary_computer as pc
# ODC tools
import odc
from odc.geo.geobox import GeoBox
from odc.stac import load
# Geospatial librairies
import geopandas as gpd
import rasterio
from rasterio.crs import CRS
from rasterio.features import rasterize
from shapely.geometry import box


def def_geobox(bbox, crs_out, resolution, shape=None):
    """
    This function creates an odc geobox.

    Args:
        bbox (list): coordinates of a bounding box.
        crs_out (str): CRS of output coordinates.
        resolution (float): output spatial resolution.
        shape (tuple, optional): output image size in pixels (x, y). Defaults to `None`.

    Returns:
        geobox (odc.geo.geobox.GeoBox): geobox object
    """

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

        newbbox = [min_x, min_y, max_x, max_y]
    else:
        newbbox = bbox

    geobox = GeoBox.from_bbox(odc.geo.geom.BoundingBox(*newbbox),
                              crs=crs,
                              resolution=resolution)
    return geobox


class Csv2gdf:
    """
    This class aims to load csv tables with geographic coordinates into GeoDataFrame object.

    Attributes:
        crs_in (int): CRS of coordinates described in the csv table.
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
        Initialize the attributes of `Csv2gdf`.

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
            box (shapely.geometry.box): bbox.
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
        __items_to_array(self): convert stac items into xarray dataset.
        __to_df(self, array_type): convert xarray dataset into pandas dataframe.
        searchItems(self, bbox_latlon, date_start='2023-01', date_end='2023-12', **kwargs): search items into a stac collection.
        loadPatches(self, bbox, dimx=5, dimy=5, resolution=10, crs_out=3035): extract xarray dataset according to predefined height and width dimensions.
        loadImgs(self, bbox, resolution=10, crs_out=3035): extract xarray dataset according to the feature's bounding box.
        to_csv(self, outdir, gid=None, array_type='image'): export xarray dataset into csv file.
        to_nc(self, array_type, gid, outdir): export xarray dataset into netcdf file.

    Example:
        >>> stacObj = StacAttack()
        >>> stacObj.searchItems(aoi_bounds_4326)
        >>> stacObj.loadPatches(aoi_bounds, 10, 10)
    """

    def __init__(self, provider='mpc',
                       collection='sentinel-2-l2a',
                       key_sat='s2',
                       bands=['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'SCL']
                ):
        """
        Initialize the attributes of `StacAttack`.

        Args:
            provider (str, optional): stac provider. Defaults to 'mpc'.
                Can be one of the following: 'mpc', 'aws'.
            collection (str, optional): stac collection. Defaults to 'sentinel-2-l2a'.
            bands (list, optional): name of the field describing Y coordinates. 
                Defaults to ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'SCL']
        """
        self.prov_stac = {'mpc':{'stac': 'https://planetarycomputer.microsoft.com/api/stac/v1',
                                 'coll': collection,
                                 'key_sat':key_sat,
                                 'modifier': pc.sign_inplace,
                                 'patch_url': pc.sign},
                          'aws':{'stac': 'https://earth-search.aws.element84.com/v1/',
                                 'coll': collection,
                                 'key_sat':key_sat,
                                 'modifier': None,
                                 'patch_url': None}
                         }
        self.stac = self.prov_stac[provider]
        self.catalog = Client.open(self.stac['stac'], modifier=self.stac['modifier'])
        self.bands = bands
        self.stac_conf = {'chunks_size':612, 'dtype':"uint16", 'nodata':0}

    def __items_to_array(self, geobox):
        """
        Convert stac items to xarray dataset.

        Args:
            geobox (odc.geo.geobox.GeoBox): odc geobox that specifies bbox, crs, spatial res. and dimensions.

        Returns:
            arr (xarray.Dataset): xarray dataset of satellite time-series.
        """
        arr = load(self.items,
                   bands=self.bands,
                   groupby="solar_day",
                   chunks={"x": self.stac_conf['chunks_size'], 
                           "y": self.stac_conf['chunks_size']},
                   patch_url=self.stac['patch_url'],
                   dtype=self.stac_conf['dtype'],
                   nodata=self.stac_conf['nodata'],
                   geobox=geobox
                  )

        return arr

    def __getItemsProperties(self):
        """
        Get item properties

        Returns:
            StacAttack.items_prop (dataframe): dataframe of image properties
        """
        self.items_prop = pd.DataFrame(self.items[0].properties)
        for it in self.items[1:]:
            new_df = pd.DataFrame(it.properties)
            self.items_prop = pd.concat([self.items_prop, new_df], ignore_index=True)
        self.items_prop['date'] = (self.items_prop['datetime']).apply(
            lambda x: int(datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()*1e9))

    def searchItems(self, bbox_latlon, date_start=datetime(2023, 1, 1), date_end=datetime(2023, 12, 31), **kwargs):
        """
        Get list of stac collection's items.

        Args:
            bbox_latlon (list): coordinates of bounding box.
            date_start (str, optional): start date. Defaults to '2023-01'.
            date_end (str, optional): end date. Defaults to '2023-12'.
            **kwargs: others stac compliant arguments.

        Returns:
            StacAttack.items (pystac.ItemCollection): list of stac collection items.
        """
        self.startdate = date_start
        self.enddate = date_end
        time_range = [self.startdate, self.enddate]
        query = self.catalog.search(collections=[self.stac['coll']],
                                    datetime=time_range,
                                    bbox=bbox_latlon,
                                    **kwargs
                                   )
        self.items = list(query.items())
        self.__getItemsProperties()

    def __checkS2shift(self, shift_value=1):
        """
        to fill
        """
        self.items_prop['shift'] = np.where(
            (self.items_prop[f'{self.stac["key_sat"]}:processing_baseline'].astype(float) >= 4.),
            shift_value,
            0)

        self.fixdate = self.items_prop[self.items_prop['shift']==shift_value]['date'].tolist()
        self.fixdate = [datetime.fromtimestamp(date_unix/1e9) for date_unix in self.fixdate]

    def fixS2shift(self, shiftval=-1000, minval=1, **kwargs):
        """
        Fix Sentinel-2 radiometric offset applied since the ESA Processing Baseline 04.00. 
        For more information: https://sentinels.copernicus.eu/web/sentinel/-/copernicus-sentinel-2-major-products-upgrade-upcoming

        Args:
            shiftval (int): radiometric offset value. Defaults to -1000.
            minval (int): minimum radiometric value. Deafeults to 1.
            **kwargs: other arguments

        Returns: StacAttack.image with corrected radiometric values.
        """
        def operation(val):
            return np.maximum(minval, val + shiftval)

        self.__checkS2shift()
        for var_name in self.image.data_vars:
            self.image[var_name].loc[{'time': self.fixdate}] = operation(self.image[var_name].loc[{'time': self.fixdate}])


    def loadPatches(self, bbox, dimx=5, dimy=5, resolution=10, crs_out=3035):
        """
        Load patches with predefined pixels dimensions (x, y)

        Args:
            bbox (list): coordinates of bounding box in the output crs.
            dimx (int, optional): number of pixels in columns. Defaults to 5.
            dimy (int, optional): number of pixels in rows. Defaults to 5.
            resolution (float, optional): spatial resolution (in crs unit). Defaults to 10.
            crs_out (int, optional): CRS of output coordinates. Defaults to 3035.

        Returns:
            StacAttack.geobox (odc.geo.geobox.GeoBox): geobox object.
            StacAttack.patch (xarray.Dataset): time-series patch.
        """
        shape = (dimx, dimy)
        self.geobox = def_geobox(bbox, crs_out, resolution, shape)
        self.patch = self.__items_to_array(self.geobox)

    def loadImgs(self, bbox, resolution=10, crs_out=3035):
        """
        Load time-series images with dimensions that fit with bounding box.

        Args:
            bbox (list): coordinates of bounding box in the output crs.
            resolution (float, optional): spatial resolution (in crs unit). Defaults to 10.
            crs_out (int, optional): CRS of output coordinates. Defaults to 3035.

        Returns:
            StacAttack.geobox (odc.geo.geobox.GeoBox): geobox object.
            StacAttack.image (xarray.Dataset): time-series image.
        """
        self.geobox = def_geobox(bbox, crs_out, resolution)
        self.image = self.__items_to_array(self.geobox)

    def __to_df(self, array_type):
        """
        Convert xarray dataset into pandas dataframe

        Args:
            array_type (str): xarray dataset name.
                Can be one of the following: 'patch', 'image'.

        Returns:
            df (dataframe): pandas dataframe object.
        """
        e_array = getattr(self, array_type)
        array_trans = e_array.transpose('time', 'y', 'x')
        df = array_trans.to_dataframe()
        return df

    def to_csv(self, outdir, gid=None, array_type='image', id_point='station_id'):
        """
        Convert xarray dataset into csv file.

        Args:
            outdir (str): output directory.
            gid (str, optional): column name of ID. Defaults to `None`.
            array_type (str, optional): xarray dataset name. Defaults to 'image'.
                Can be one of the following: 'patch', 'image'.
        """
        df = self.__to_df(array_type)
        df = df.reset_index()
        df['ID'] = df.index
        df[id_point] = gid
        if gid is not None:
            df.to_csv(os.path.join(outdir, f'id_{gid}_{array_type}.csv'))
        else:
            df.to_csv(os.path.join(outdir, f'id_none_{array_type}.csv'))

    def to_nc(self, outdir, gid=None, array_type='image'):
        """
        Convert xarray dataset into netcdf file.

        Args:
            outdir (str): output directory.
            gid (str, optional): column name of ID. Defaults to `None`.
            array_type (str, optional): xarray dataset name. Defaults to 'image'.
                Can be one of the following: 'patch', 'image'.
        """
        e_array = getattr(self, array_type)
        e_array.to_netcdf(f"{outdir}/S2_fid-{gid}_{array_type}_{self.startdate}-{self.enddate}.nc")


class Labels:
    """
    This class aims to produce a image of labels from a vector file.

    Attributes:
        gdf (geodataframe) : vector layer

    Methods:
        to_raster(self, id_field, geobox, filename, outdir, crs='EPSG:3035', driver="GTiff"): 
            Convert a geodataframe into raster while keeping a column attribute as pixel values.

    Example:
        >>> vlayer = Labels(geodataframe)
        >>> vlayer.to_raster('id', geobox, 'output.tif', 'my_dir')
    """

    def __init__(self, geolayer):
        """
        Initialize the attributes of `Labels`.

        Args:
            geolayer (str or geodataframe): vector layer to rasterize.

        Returns:
            Labels.gdf (geodataframe): geodataframe.
        """
        if isinstance(geolayer, pd.core.frame.DataFrame):
            self.gdf = geolayer.copy()
        else:
            self.gdf = gpd.read_file(geolayer)

    def to_raster(self, id_field, geobox, filename, outdir, crs='EPSG:3035', driver="GTiff"):
        """
        Convert geodataframe into raster file.

        Args:
            id_field (str): column name to keep as pixels values.
            geobox (odc.geo.geobox.GeoBox): geobox object.
            filename (str): output raster filename.
            outdir (str): output directory.
            crs (str, optional): output crs. Defaults to "EPSG:3035".
            driver (str, optional): output raster format (gdal standard). Defaults to "GTiff".
        """
        shapes = ((geom, value) for geom, value in zip(self.gdf.geometry, self.gdf[id_field]))
        rasterized = rasterize(shapes, 
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
