import pandas as pd
import geopandas as gpd
from shapely.geometry import box


class Csv2gdf():

    def __init__(self, csv_file, id_name, x_name, y_name, crs_in):
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

        if outfile is not None:
            self.gdf.to_file(outfile, driver="GeoJSON", encoding='utf-8')
            
    def set_buffer(self, radius, outfile=None):
        self.buffer = self.gdf.copy()
        self.buffer['geometry'] = self.buffer.geometry.buffer(radius)
        
        if outfile is not None:
            self.buffer.to_file(outfile, driver="GeoJSON", encoding='utf-8')
            
    def set_bbox(self, polygon_layer, outfile=None):
        self.bbox = polygon_layer.copy()
        self.bbox['geometry'] = self.buffer.apply(self.__create_bounding_box, axis=1)            
        
        if outfile is not None:
            self.bbox.to_file(outfile, driver="GeoJSON", encoding='utf-8')
            
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
    