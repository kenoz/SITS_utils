import os
import sys
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
# Dask
import dask


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


def compare_crs(crs_a, crs_b):
    if crs_a != crs_b:
        raise ValueError(f"CRS mismatch: {crs_a} != {crs_b}")


class Gdfgeom:
    """
    This class aims to calculate vector's buffers and bounding box.

    Attributes:
        buffer (GeoDataFrame): vector layer with buffer.
        bbox (GeoDataFrame): vector layer's bounding box.
    """

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


class Vec2gdf(Gdfgeom):
    """
    This class aims to load a vector file as a GeoDataFrame object. 
    It inherits methods and attributes from ``Gdfgeom`` class. 

    Example:
        >>> v_path = '<vector file path>'
        >>> geotable = Vec2gdf(v_path)
    """

    def __init__(self, vec_file):
        self.gdf = gpd.read_file(vec_file)


class Csv2gdf(Gdfgeom):
    """
    This class aims to load csv tables with geographic coordinates into GeoDataFrame object. 
    It inherits methods and attributes from ``Gdfgeom`` class

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
                       bands=['B02', 'B03', 'B04', 'B05', 'B06', 
                              'B07', 'B08', 'B8A', 'B11', 'B12', 'SCL']
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

    def searchItems(self, bbox_latlon, date_start=datetime(2023, 1, 1), 
                    date_end=datetime(2023, 12, 31), **kwargs):
        """
        Get list of stac collection's items.

        Args:
            bbox_latlon (list): coordinates of bounding box.
            date_start (datetime.datetime, optional): start date. Defaults to '2023-01'.
            date_end (datetime.datetime, optional): end date. Defaults to '2023-12'.
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

    def loadCube(self, bbox, arrtype='image', dimx=5, dimy=5, resolution=10, crs_out=3035):
        """
        Load images according to a bounding box, with in option predefined pixels dimensions (x, y).

        Args:
            bbox (list): coordinates of bounding box [xmin, ymin, xmax, ymax] in the output crs unit.
            arrtype (string, optional: xarray dataset name. Defaults to 'image'.
                Can be one of the following: 'patch', 'image', 'masked'.
            dimx (int, optional): number of pixels in columns. Defaults to 5.
            dimy (int, optional): number of pixels in rows. Defaults to 5.
            resolution (float, optional): spatial resolution (in crs unit). Defaults to 10.
            crs_out (int, optional): CRS of output coordinates. Defaults to 3035.

        Returns:
            odc.geo.geobox.GeoBox: geobox object ``StacAttack.geobox``.
            xarray.Dataset: time-series image ``StacAttack.cube``.

        Example:
            >>> aoi_bounds = [0, 0, 1, 1]
            >>> stacObj.loadCube(aoi_bounds, arrtype='patch', dimx=10, dimy=10)
        """
        self.arrtype = arrtype

        if arrtype == 'image':
            self.geobox = def_geobox(bbox, crs_out, resolution)
        if arrtype == 'patch':
            shape = (dimx, dimy)
            self.geobox = def_geobox(bbox, crs_out, resolution, shape)

        self.cube = self.__items_to_array(self.geobox)

    def mask(self, mask_array=None, mask_band='SCL', mask_values=[3, 8, 9, 10]):
        """
        Load binary mask.

        Args:
            mask_array (xarray.Dataarray, optional): xarray.dataarray binanry mask 
                (with same dimensions as ``StacAttack.cube``). Defaults to None.
            mask_band (string, optional): band name used as a mask (i.e. 'SCL' for Sentinel-2). 
                Defaults to 'SCL'.
            mask_values (list, optional): band values related to masked pixels.
                Defaults to [3, 8, 9, 10].

        Returns:
            xarray.Dataarray: time-series of binary masks ``StacAttack.mask``

        Example:
            >>> stacObj.mask()
        """

        if mask_array:
            self.mask = mask_array
        else:
            band_mask = getattr(self.cube, mask_band)
            self.mask = band_mask.isin(mask_values)

    def mask_apply(self):
        """
        Apply mask pre-loaded as ``StacAttack.mask`` on the satellite time-series ``StacAttack.cube``.

        Example:
            >>> stacObj.mask()
            >>> stacObj.mask_apply()
        """
        self.cube = self.cube.where(~self.mask)

    def gapfill(self, method='linear', first_last=True, **kwargs):
        """
        Gap-fill NaN pixel values through the satellite time-series.

        Args:
            method (string, optional): method to use for interpolation 
                (see ``xarray.DataArray.interpolate_na``). Defaults to 'linear'.
            first_last (bool, optional): Interpolation of the first and
                last image of the satellite time-series with
                ``xarray.DataArray.bfill`` and ``xarray.DataArray.ffill``.
                Defaults to True.
            **kwargs: other arguments of ``xarray.DataArray.interpolate_na``.

        Example:
            >>> stacObj.gapfill()
        """
        self.cube = self.cube.interpolate_na()

        if first_last:
            self.cube = self.cube.bfill(dim='time')
            self.cube = self.cube.ffill(dim='time')

    def __to_df(self):
        """
        Convert xarray dataset into pandas dataframe

        Args:
            array_type (str): xarray dataset name.
                Can be one of the following: 'patch', 'image', 'masked'.

        Returns:
            DataFrame: pandas dataframe object (df).
        """
        array_trans = self.cube.transpose('time', 'y', 'x')
        df = array_trans.to_dataframe()
        return df

    def to_csv(self, outdir, gid=None, id_point='station_id'):
        """
        Convert xarray dataset into csv file.

        Args:
            outdir (str): output directory.
            gid (str, optional): column name of ID. Defaults to `None`.

        Example:
            >>> outdir = 'output'
            >>> stacObj.to_csv(outdir)
        """
        df = self.__to_df()
        df = df.reset_index()
        df['ID'] = df.index
        df[id_point] = gid

        if gid is not None:
            df.to_csv(os.path.join(outdir, f'id_{gid}_{self.arrtype}.csv'))
        else:
            df.to_csv(os.path.join(outdir, f'id_none_{self.arrtype}.csv'))

    def to_nc(self, outdir, gid=None):
        """
        Convert xarray dataset into netcdf file.

        Args:
            outdir (str): output directory.
            gid (str, optional): column name of ID. Defaults to `None`.
            array_type (str, optional): xarray dataset name. Defaults to 'image'.
                Can be one of the following: 'patch', 'image', 'masked'.

        Example:
            >>> outdir = 'output'
            >>> stacObj.to_nc(outdir)
        """
        self.cube.to_netcdf(f"{outdir}/S2_fid-{gid}_{self.arrtype}_{self.startdate}-{self.enddate}.nc")


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

        self.crs_gdf = self.gdf.crs.to_epsg()

    def to_raster(self, id_field, geobox, filename, outdir, ext='tif', driver="GTiff"):
        """
        Convert geodataframe into raster file while keeping a column attribute as pixel values.

        Args:
            id_field (str): column name to keep as pixels values.
            geobox (odc.geo.geobox.GeoBox): geobox object.
            filename (str): output raster filename.
            outdir (str): output directory.
            ext (str, optional): raster file extension. Defaults to "tif".
            driver (str, optional): output raster format (gdal standard). Defaults to "GTiff".

        Example:
            >>> bbox = [0, 0, 1, 1]
            >>> crs_out = 3035
            >>> resolution = 10
            >>> geobox = def_geobox(bbox, crs_out, resolution)
            >>> vlayer.to_raster('id', geobox, 'output_img', 'output_dir')
        """
        self.crs_geobox = geobox.crs.to_epsg()

        #if self.crs_gdf != self.crs_geobox:
        #    self.gdf = self.gdf.to_crs(self.crs_geobox)
        #    self.crs_gdf = self.gdf.crs.to_epsg()

        # NEED TO STOP HERE IN CASE OF CRS DIFF
        try:
            compare_crs(self.crs_gdf, self.crs_geobox)
            crs_out = self.crs_geobox
        except ValueError as e:
            print(e)
            sys.exit(1)

        shapes = ((geom, value) for geom, value in zip(self.gdf.geometry, self.gdf[id_field]))
        rasterized = rasterize(shapes,
                               out_shape=(geobox.height, geobox.width),
                               transform=geobox.transform,
                               fill=0,
                               all_touched=False,
                               dtype='uint16')

        # Write the rasterized feature to a new raster file
        with rasterio.open(os.path.join(outdir, f"{filename}.{ext}"), 'w',
                           driver=driver, crs=f"EPSG:{crs_out}",
                           transform=geobox.transform, dtype=rasterio.uint16,
                           count=1, width=geobox.width,
                           height=geobox.height) as dst:
            dst.write(rasterized, 1)


class Multiproc:
    """
    This class aims to parallelize the production of images or patches.

    Args:
        array_type (str): xarray dataset name.
                Can be one of the following: 'patch', 'image'.
        fext (str): output file format:
                Can be one of the following: 'nc', 'csv'
        outdir (str): output directory.

    Example:
        >>> mproc = Multiproc('patch', 'nc', 'output')
    """

    def __init__(self, array_type, fext, outdir):
        """ Initialize the attributes of ``Multiproc``."""
        self.arrtype = array_type
        self.outdir = outdir
        self.fext = fext
        self.fetch_dask = []
        self.label = 0
        self.sa_kwargs = {}
        self.si_kwargs = {}
        self.lc_kwargs = {}
        self.ma_kwargs = {}
        self.gf_kwargs = {}
        self.tr_kwargs = {}

    def add_label(self, geolayer, id_field):
        """
        Export an image of labels with the same dimensions than the datacube,
        by calling the method ``Labels.to_raster()``.

        Args:
            geolayer (GeoDataFrame): vector file.
            id_field (str): attribute field name.

        Example:
            >>> mproc = Multiproc('patch', 'nc', 'output')
            >>> mproc.add_label(vlayer, 'myfield')
        """
        self.geolayer = geolayer
        self.id_field = id_field
        self.label = 1

    def addParams_stacAttack(self, provider='mpc', collection='sentinel-2-l2a', key_sat='s2',
                             bands=['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 
                                    'B08', 'B8A', 'B11', 'B12', 'SCL']):
        """
        Add optional parameters for ``StacAttack class instance``
        called through ``Multiproc.fetch_func()``.

        Args:
            provider (str, optional): stac provider. Defaults to 'mpc'.
                Can be one of the following: 'mpc' (Microsoft Planetary Computer), 'aws' (Amazon Web Services).
            collection (str, optional): stac collection. Defaults to 'sentinel-2-l2a'.
            bands (list, optional): name of the field describing Y coordinates.
                Defaults to ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12', 'SCL']

        Example:
            >>> mproc = Multiproc('patch', 'nc', 'output')
            >>> mproc.addParams_stacAttack(bands=['B02', 'B03', 'B04'])
        """
        self.sa_kwargs.update({'provider': provider, 'collection': collection, 'key_sat': key_sat, 'bands': bands})

    def addParams_searchItems(self, date_start=datetime(2023, 1, 1), date_end=datetime(2023, 12, 31), **kwargs):
        """
        Add optional parameters for ``StacAttack.searchItems()``
        called through ``Multiproc.fetch_func()``.

        Args:
            date_start (datetime.datetime, optional): start date. Defaults to '2023-01'.
            date_end (datetime.datetime, optional): end date. Defaults to '2023-12'.
            **kwargs (optional): others stac compliant arguments, 
                e.g. ``query`` parameters to filter according to cloud %.

        Example:
            >>> mproc = Multiproc('patch', 'nc', 'output')
            >>> mproc.addParams_searchItems(date_start=datetime(2016, 1, 1), query={"eo:cloud_cover": {"lt": 20}})
        """
        self.si_kwargs.update({'date_start': date_start, 'date_end': date_end})
        self.si_kwargs.update({k: v for k, v in kwargs.items()})

    def addParams_loadCube(self, dimx=5, dimy=5, resolution=10, crs_out=3035):
        """
        Add optional parameters for ``StacAttack.loadCube()``
        called through ``Multiproc.fetch_func()``.

        Args:
            dimx (int, optional): number of pixels in columns. Defaults to 5.
            dimy (int, optional): number of pixels in rows. Defaults to 5.
            resolution (float, optional): spatial resolution (in crs unit). Defaults to 10.
            crs_out (int, optional): CRS of output coordinates. Defaults to 3035.

        Example:
            >>> mproc = Multiproc('patch', 'nc', 'output')
            >>> mproc.addParams_loadCube(dimx=20, dimy=20):
        """
        self.lc_kwargs.update({'dimx': dimx, 'dimy': dimy,
                               'resolution': resolution, 'crs_out': crs_out})

    def addParams_mask(self, mask_array=None, mask_band='SCL', mask_values=[3, 8, 9, 10]):
        """
        Add optional parameters for ``StacAttack.mask()``
        called through ``Multiproc.fetch_func()``.
        
        Args:
            mask_array (xarray.Dataarray, optional): xarray.dataarray binanry mask 
                (with same dimensions as ``StacAttack.cube``). Defaults to None.
            mask_band (string, optional): band name used as a mask (i.e. 'SCL' for Sentinel-2). 
                Defaults to 'SCL'.
            mask_values (list, optional): band values related to masked pixels.
                Defaults to [3, 8, 9, 10].

        Example:
            >>> mproc = Multiproc('patch', 'nc', 'output')
            >>> mproc.addParams_mask(mask_values=[0]):
        """
        self.ma_kwargs.update({'mask_array': mask_array,
                               'mask_band': mask_band,
                               'mask_values': mask_values})

    def addParams_gapfill(self, method='linear', first_last=True, **kwargs):
        """
        Add optional parameters for ``StacAttack.gapfill()``
        called through ``Multiproc.fetch_func()``.

        Args:
            method (string, optional): method to use for interpolation 
                (see ``xarray.DataArray.interpolate_na``). Defaults to 'linear'.
            first_last (bool, optional): Interpolation of the first and
                last image of the satellite time-series with
                ``xarray.DataArray.bfill`` and ``xarray.DataArray.ffill``.
                Defaults to True.
            **kwargs: other arguments of ``xarray.DataArray.interpolate_na``.

        Example:
            >>> mproc = Multiproc('patch', 'nc', 'output')
            >>> mproc.addParams_gapfill(method='nearest', first_last=False):
        """
        self.gf_kwargs.update({'method': method,
                               'first_last': first_last,
                               'mask_values': mask_values})
        self.gf_kwargs.update({k: v for k, v in kwargs.items()})

    def addParams_to_raster(self, ext='tif', driver="GTiff"):
        """
        Add optional parameters for ``Labels.to_raster()``
        called through ``Multiproc.fetch_func()``.

        Args:
            ext (str, optional): raster file extension. Defaults to "tif".
            driver (str, optional): output raster format (gdal standard). Defaults to "GTiff".

        Example:
            >>> mproc = Multiproc('patch', 'nc', 'output')
            >>> mproc.addParams_to_raster(driver="COG")
        """
        self.si_kwargs.update({'ext': ext, 'driver': driver})

    def __fdask(self, aoi_latlong, aoi_proj, gid, mask=False, gapfill=False, **kwargs):
        """
        Request items in STAC catalog and convert it as an image or patch.

        Args:
            aoi_latlong (list): coordinates of bounding box.
            aoi_proj (list): coordinates of bounding box [xmin, ymin, xmax, ymax] in the output crs.
            gid (int): image/patch index.
            mask (bool, optional): calculate and apply binary masks. Defaults to False.
            gapfill (bool, optional): fill in NaNs (masked pixels) by interpolating according 
                to different methods. Defaults to False.
            **kwargs (dict): additional arguments (i.e. ``StacAttack.searchItems()``,
                                                        ``StacAttack.loadCube()``,
                                                        ``Labels.to_raster()``).
        """
        # searchItems
        self.si_kwargs.update(
            {k: v for k, v in kwargs.items() if k in ['date_start',
                                                      'date_end',
                                                      'query']}
        )

        # loadCube
        self.lc_kwargs.update(
            {k: v for k, v in kwargs.items() if k in ['dimx',
                                                      'dimy',
                                                      'resolution',
                                                      'crs_out']}
        )

        # to_raster
        self.tr_kwargs.update(
            {k: v for k, v in kwargs.items() if k in ['ext',
                                                      'driver']}
        )

        # StacAttack init
        self.sa_kwargs.update(
            {k: v for k, v in kwargs.items() if k in ['provider',
                                                      'collection',
                                                      'key_sat',
                                                      'bands']}
        )

        imgcoll = StacAttack(**self.sa_kwargs)
        imgcoll.searchItems(aoi_latlong, **self.si_kwargs)
        imgcoll.loadCube(aoi_proj, arrtype=self.arrtype, **self.lc_kwargs)

        if mask:
            imgcoll.mask(**self.ma_kwargs)
            imgcoll.mask_apply(**self.gf_kwargs)
        if gapfill:
            imgcoll.gapfill()

        if self.fext == 'nc':
            imgcoll.to_nc(self.outdir, gid)
        elif self.fext == 'csv':
            imgcoll.to_csv(self.outdir, gid, id_point='station_id')

        if self.label == 1:
            labr = Labels(self.geolayer)
            filename = f"label_{self.id_field}_{gid}"
            labr.to_raster(self.id_field, imgcoll.geobox, filename, 
                           self.outdir, **self.tr_kwargs)

    def fetch_func(self, aoi_latlong, aoi_proj, gid, mask=False, gapfill=False, **kwargs):
        """
        Call of ``dask.delayed`` to convert the ``Multiproc.__fdask()`` function 
        into a delayed object, allowing for lazy evaluation and parallel execution, 
        thus optimizing computational workflows.

        Args:
            aoi_latlong (list): coordinates of bounding box.
            aoi_proj (list): coordinates of bounding box [xmin, ymin, xmax, ymax] in the output crs.
            gid (int): image/patch index.
            **kwargs (dict): additional arguments (i.e. ``StacAttack.searchItems()``,
                                                        ``StacAttack.loadImgs()``,
                                                        ``StacAttack.loadPatches()``).
        Returns:
            Multiproc.fetch_dask: list of ``dask.delayed`` function's instances.

        Example:
            >>> for bboxes, gid in enumerate(my_df['bboxes']):
                    mproc.fetch_func(bboxes[0], bboxes[1], gid)
        """
        single = dask.delayed(self.__fdask)(aoi_latlong, aoi_proj, gid, mask, gapfill, **kwargs)
        self.fetch_dask.append(single)

    def del_func(self):
        """
        Clear ``Multiproc.fetch_dask``, the list of ``dask.delayed`` function's 
        instances.
        """
        self.fetch_dask.clear()

    def dask_compute(self, scheduler_type='processes'):
        """
        Call of ``dask.compute`` to trigger the actual execution of
        delayed tasks (i.e. ``Multiproc.fetch_dask``), gathering their results 
        into a final output.

        Args:
            scheduler_type (str): type of scheduler. Defaults to 'processes'.
                    Can be one of the following: - Single-threaded Scheduler 'single-threaded' or 'sync': 
                                                        - Runs computations in a single thread without parallelism.
                                                        - Suitable for debugging or when parallelism isn't required.
                                                 - Threaded Scheduler 'threads':
                                                         - Utilizes a pool of threads to execute tasks concurrently.
                                                         - Good for I/O-bound tasks and when tasks release the Global Interpreter Lock (GIL). 
                                                 - Multiprocessing Scheduler 'processes':
                                                         - Uses a pool of separate processes to execute tasks in parallel.
                                                         - Suitable for CPU-bound tasks and when tasks are limited by the GIL.
                                                 - Distributed Scheduler 'distributed':
                                                         - Uses a distributed cluster to execute tasks.
                                                         - Best for large-scale computations across multiple machines.
        Example:
            >>> mproc.dask_compute()
        """
        results_dask = dask.compute(*self.fetch_dask, scheduler=scheduler_type)
        return results_dask