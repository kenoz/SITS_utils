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


def def_geobox(bbox, crs_out=3035, resolution=10, shape=None):
    """
    This function creates an odc geobox.

    Args:
        bbox (list): coordinates of a bounding box in CRS units.
        crs_out (str, optional): CRS (EPSG code) of output coordinates. Defaults to 3035.
        resolution (float, optional): output spatial resolution in CRS units. Defaults to 10 (meters).
        shape (tuple, optional): output image size in pixels (x, y). Defaults to `None`.

    Returns:
        odc.geo.geobox.GeoBox: geobox object

    Example:
        >>> bbox = [100, 100, 200, 220]
        >>> crs_out = 3035
        >>> # output geobox closest to the input bbox
        >>> geobox = def_geobox(bbox, crs_out)

        >>> # output geobox with the same dimensions (number of rows and columns) 
        >>> # as the input shape.
        >>> geobox = def_geobox(bbox, crs_out, shape=(10, 10))
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
        table (DataFrame): DataFrame object.

    Args:
        csv_file (str): csv filepath.
        x_name (str): name of the field describing X coordinates.
        y_name (str): name of the field describing Y coordinates.
        crs_in (int): CRS of coordinates described in the csv table.
        id_name (str, optional): name of the ID field. Defaults to "no_id".

    Example:
        >>> csv_file = 'example.csv'
        >>> crs_in = 4326
        >>> geotable = Csv2gdf(csv_file, 'longitude', 'latitude', crs_in)
    """

    def __init__(self, csv_file, x_name, y_name, crs_in, id_name='no_id'):
        """
        Initialize the attributes of `Csv2gdf`.
        """
        self.crs_in = crs_in
        self.table = pd.read_csv(csv_file, encoding= 'unicode_escape')
        self.table = self.table.rename(columns={x_name: 'coord_X',
                                                y_name: 'coord_Y',
                                                id_name: 'gid'})

    def set_gdf(self, crs_out):
        """
        Convert the class attribute ``Csv2gdf.table`` (DataFrame) into GeoDataFrame object, 
        in the specified output CRS projection.

        Args:
            crs_out (int): output CRS of GeoDataFrame.
            outfile (str, optional): Defaults to `None`.

        Returns:
            GeoDataFrame: GeoDataFrame object ``Csv2gdf.gdf``.

        Example:
            >>> geotable.set_gdf(3035)
        """

        self.gdf = gpd.GeoDataFrame(self.table,
                                    geometry=gpd.points_from_xy(self.table.coord_X,
                                                                self.table.coord_Y)
                                   )
        self.gdf = self.gdf.set_crs(self.crs_in, allow_override=True)
        self.gdf = self.gdf.to_crs(crs_out)

    def set_buffer(self, df_attr, radius):
        """
        Calculate buffer geometries for each ``Csv2gdf``'s GeoDataFrame feature.

        Args:
            df_attr (str): GeoDataFrame attribute of class ``Csv2gdf``.
                Can be one of the following: 'gdf', 'buffer', 'bbox'.
            radius (float): buffer distance in CRS unit.
            outfile (str, optional): ouput filepath. Defaults to `None`.

        Returns:
            GeoDataFrame: GeoDataFrame object ``Csv2gdf.buffer``.

        Example:
            >>> geotable.set_buffer('gdf', 100)
        """

        df = getattr(self, df_attr)
        self.buffer = df.copy()
        self.buffer['geometry'] = self.buffer.geometry.buffer(radius)

    def set_bbox(self, df_attr):
        """
        Calculate the bounding box for each ``Csv2gdf``'s GeoDataFrame feature.

        Args:
            df_attr (str): GeoDataFrame attribute of class ``Csv2gdf``.
                Can be one of the following: 'gdf', 'buffer', 'bbox'.
            outfile (str, optional): ouput filepath. Defaults to `None`.

        Returns:
            GeoDataFrame: GeoDataFrame object ``Csv2gdf.bbox``.

        Example:
            >>> geotable.set_bbox('buffer')
        """

        df = getattr(self, df_attr)
        self.bbox = df.copy()
        self.bbox['geometry'] = self.bbox.apply(self.__create_bounding_box, axis=1)

    def to_vector(self, df_attr, outfile=None, driver="GeoJSON"):
        """
        Write a ``Csv2gdf``'s GeoDataFrame layer as a vector file.

        Args:
            df_attr (str): GeoDataFrame attribute of class ``Csv2gdf``.
                Can be one of the following: 'gdf', 'buffer', 'bbox'.
            outfile (str, optional): Output path. Defaults to `None`.
            driver (str, optional): Output vector file format (see *GDAL/OGR Vector drivers*: https://gdal.org/drivers/vector/index.html). Defaults to "GeoJSON".

        Example:
            >>> filename = 'mygeom'
            >>> geotable.to_vector('gdf', f'output/{filename}_gdf.geojson')
            >>> geotable.to_vector('buffer', f'output/{filename}_buffer.geojson')
            >>> geotable.to_vector('bbox', f'output/{filename}_bbox.geojson')
        """

        df = getattr(self, df_attr)
        df.to_file(outfile, driver=driver, encoding='utf-8')

    def del_rows(self, col_name, rows_values):
        """
        Drop rows from ``Csv2gdf.table`` according to a column's values.

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
            shapely.geometry.box: bbox.
        """

        xmin, ymin, xmax, ymax = row.geometry.bounds
        return box(xmin, ymin, xmax, ymax)


class StacAttack:
    """
    This class aims to request time-series datasets on STAC catalog and store it as image or csv files.

    Attributes:
        stac_conf (dict): parameters for building datacube (xArray) from STAC items.

    Args:
        provider (str, optional): stac provider. Defaults to 'mpc'.
            Can be one of the following: 'mpc' (Microsoft Planetary Computer), 'aws' (Amazon Web Services).
        collection (str, optional): stac collection. Defaults to 'sentinel-2-l2a'.
        bands (list, optional): name of the field describing Y coordinates.
            Defaults to ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'SCL']

    Example:
        >>> stacObj = StacAttack()
    """

    def __init__(self, provider='mpc',
                       collection='sentinel-2-l2a',
                       key_sat='s2',
                       bands=['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'SCL']
                ):
        """
        Initialize the attributes of `StacAttack`.
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
            xarray.Dataset: xarray dataset of satellite time-series.
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
            DataFrame: dataframe of image properties ``StacAttack.items_prop``.
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
            pystac.ItemCollection: list of stac collection items ``StacAttack.items``.

        Example:
            >>> stacObj.searchItems(aoi_bounds_4326)
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
        Check whether the Sentinel-2 images values need to be shifted according to the processing baseline version.

        Args:
            shift_value (int): number used to flag images that need to be shifted

        Returns:
            list: list of Sentinel-2 acquisition dates
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
            minval (int): minimum radiometric value. Defaults to 1.
            **kwargs: other arguments

        Returns: ``StacAttack.image`` with corrected radiometric values.
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
            bbox (list): coordinates of bounding box [xmin, ymin, xmax, ymax] in the output crs unit.
            dimx (int, optional): number of pixels in columns. Defaults to 5.
            dimy (int, optional): number of pixels in rows. Defaults to 5.
            resolution (float, optional): spatial resolution (in crs unit). Defaults to 10.
            crs_out (int, optional): CRS of output coordinates. Defaults to 3035.

        Returns:
            odc.geo.geobox.GeoBox: geobox object ``StacAttack.geobox``.
            xarray.Dataset: time-series patch ``StacAttack.patch``.

        Example:
            >>> aoi_bounds = [0, 0, 1, 1]
            >>> stacObj.loadPatches(aoi_bounds, 10, 10)
        """
        shape = (dimx, dimy)
        self.geobox = def_geobox(bbox, crs_out, resolution, shape)
        self.patch = self.__items_to_array(self.geobox)

    def loadImgs(self, bbox, resolution=10, crs_out=3035):
        """
        Load time-series images with dimensions that fit with bounding box.

        Args:
            bbox (list): coordinates of bounding box [xmin, ymin, xmax, ymax] in the output crs unit.
            resolution (float, optional): spatial resolution (in crs unit). Defaults to 10.
            crs_out (int, optional): CRS of output coordinates. Defaults to 3035.

        Returns:
            odc.geo.geobox.GeoBox: geobox object ``StacAttack.geobox``.
            xarray.Dataset: time-series image ``StacAttack.image``.
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
            DataFrame: pandas dataframe object (df).
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

        Example:
            >>> outdir = 'output'
            >>> stacObj.to_csv(outdir)
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

        Example:
            >>> outdir = 'output'
            >>> stacObj.to_nc(outdir)
        """
        e_array = getattr(self, array_type)
        e_array.to_netcdf(f"{outdir}/S2_fid-{gid}_{array_type}_{self.startdate}-{self.enddate}.nc")


class Labels:
    """
    This class aims to produce a image of labels from a vector file.

    Args:
        geolayer (str or geodataframe): vector layer to rasterize.

    Returns:
        GeoDataFrame: geodataframe ``Labels.gdf``.

    Example:
        >>> geodataframe = <gdf object>
        >>> vlayer = Labels(geodataframe)

        >>> vector_file = 'myVector.shp'
        >>> vlayer = Labels(vector_file)
    """

    def __init__(self, geolayer):
        """
        Initialize the attributes of `Labels`.
        """
        if isinstance(geolayer, pd.core.frame.DataFrame):
            self.gdf = geolayer.copy()
        else:
            self.gdf = gpd.read_file(geolayer)

    def to_raster(self, id_field, geobox, filename, outdir, crs='EPSG:3035', driver="GTiff"):
        """
        Convert geodataframe into raster file while keeping a column attribute as pixel values.

        Args:
            id_field (str): column name to keep as pixels values.
            geobox (odc.geo.geobox.GeoBox): geobox object.
            filename (str): output raster filename.
            outdir (str): output directory.
            crs (str, optional): output crs. Defaults to "EPSG:3035".
            driver (str, optional): output raster format (gdal standard). Defaults to "GTiff".

        Example:
            >>> bbox = [0, 0, 1, 1]
            >>> crs_out = 3035
            >>> resolution = 10
            >>> geobox = def_geobox(bbox, crs_out, resolution)
            >>> vlayer.to_raster('id', geobox, 'output.tif', 'output')
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
