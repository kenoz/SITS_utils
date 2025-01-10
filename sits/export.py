import xarray as xr
import dask.array as dask_array
import geogif


class Sits_ds:
    """handle xarray.dataset"""

    def __init__(self, nc_path):
        self.ds = xr.open_dataset(nc_path, engine="netcdf4")

    def ds2da(self, keep_bands=['B04', 'B03', 'B02']):
        """
        Transform ``xarray.dataset`` into ``xarray.dataarray``
        with dimensions ordered as follows: 'time', 'band', 'y', 'x'.

        Args:
            keep_bands (list, optional): bands to keep (1 or 3 bands for gif export).

        Returns:
            Sits_ds.da: ``xarray.dataarray``.

        Example:
            >>> geo_dc = Sits_ds(netcdf_file)
            >>> geo_dc.ds2da()
        """
        sel_ds = self.ds[keep_bands]
        self.da = sel_ds.to_array(dim='band')
        self.da = self.da.transpose('time', 'band', 'y', 'x')

    def export2gif(self, imgfile=None, fps=8, robust=True, **kwargs):
        """
        Create satellite timelapse, and export it as animated GIF file.

        Args:
            imgfile (string, optional): GIF file path.
            fps (int, optional): frames per second
            robust (bool, optional): calculate vmin and vmax from the 2nd and 98th percentiles of the data. Defaults to True.

        Returns:
            Sits_ds.gif: ``IPython.display.Image`` if ``imgfile`` is None.

        Example:
            >>> geo_dc = Sits_ds(netcdf_file)
            >>> geo_dc.ds2da()
            >>> geo_dc.export2gif(imgfile='myTimeSeries.gif')
        """
        if isinstance(self.da.data, dask_array.Array):
            self.gif = geogif.dgif(self.da, fps=fps, robust=robust, **kwargs).compute()
            if imgfile:
                with open(imgfile, "wb") as f:
                    f.write(self.gif)
        else:
            self.gif = geogif.gif(self.da, fps=fps, robust=robust, to=imgfile, **kwargs)

