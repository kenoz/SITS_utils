import xarray as xr
import dask.array as dask_array
import geogif


class Sits_ds:
    """handle xarray.dataset"""

    def __init__(self, nc_path):
        self.ds = xr.open_dataset(nc_path, engine="netcdf4")

    def ds2da(self, keep_bands=['B04', 'B03', 'B02']):
        """to fill"""
        sel_ds = self.ds[keep_bands]
        self.da = sel_ds.to_array(dim='band')
        self.da = self.da.transpose('time', 'band', 'x', 'y')

    def export2gif(self, imgfile=None, fps=8, robust=True): #, bytes=True, ):
        """to fill"""
        if isinstance(self.da.data, dask_array.Array):
            self.gif = geogif.dgif(self.da, fps=fps, robust=robust).compute()
        else:
            self.gif = geogif.gif(self.da, fps=fps, robust=robust)
#        if imgfile is not None:
#            with open(imgfile, "wb") as f:
#                f.write(gif_img)
