import xarray as xr
import dask.array as dask_array
import geogif
import pandas as pd


class Sits_ds:
    """handle xarray.dataset"""

    def __init__(self, nc_path=None):
        if nc_path:
            self.ds = xr.open_dataset(nc_path, engine="netcdf4")

    def __ds2da(self, keep_bands=['B04', 'B03', 'B02']):
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

    @staticmethod
    def __blend_datasets(ds1, ds2, alpha):
        blended_vars = {var: (1 - alpha) * ds1[var] + alpha * ds2[var] for var in ds1.data_vars}

        return xr.Dataset(blended_vars, coords=ds1.coords)

    def blender(self, steps_between=5):
        """
        Generates intermediate blended frames between consecutive images 
        to achieve smooth transitions in animated GIFs.

        Args:
            steps_between (int, optional): number of intermediate blended 
                frames to generate between each pair of images. 
                Defaults to 5.

        Returns:
            Sits_ds.ds (xr.Dataset): Dataset with regular time steps.

        Example:
            >>> geo_dc = Sits_ds(netcdf_file)
            >>> geo_dc.time_interp()
            >>> geo_dc.blender()
        """
        frames = []
        for i in range(len(self.ds.time) - 1):
            ds_start = self.ds.isel(time=i)
            ds_end = self.ds.isel(time=i+1)
            frames.append(ds_start)

            # Generate blended intermediate frames
            for j in range(1, steps_between + 1):
                alpha = j / (steps_between + 1)
                frames.append(self.__blend_datasets(ds_start, ds_end, alpha))

        frames.append(self.ds.isel(time=-1))  # Add final original frame

        time_coords = [pd.Timestamp(ds.time.values) for ds in frames]
        self.ds = xr.concat(frames, dim=xr.DataArray(time_coords,
                                                     dims="time",
                                                     name="time"))

    def time_interp(self, method='slinear', nb_period=100):
        """
        Transforms the input ``Sits_ds.ds`` (xarray.Dataset) into a regular
        time-step datacube. This function resamples or interpolates the input
        Dataset to create a uniformly spaced time dimension. It is particularly
        useful for preparing data for animations, temporal analysis, or
        numerical modeling where consistent temporal intervals are required.

        Args:
            method (str, optional): interpolation method to use. Defaults to 'slinear'.
            nb_period (int, optional): number of output dates. Defaults to 100

        Returns:
            Sits_ds.ds (xr.Dataset): Dataset with regular time steps

        Example:
            >>> geo_dc = Sits_ds(netcdf_file)
            >>> geo_dc.time_interp()
        """
        new_times = pd.date_range(start=self.ds.time.min().values,
                                  end=self.ds.time.max().values,
                                  periods=nb_period)

        self.ds = self.ds.interp(time=new_times, method=method)

    def export2gif(self, imgfile=None, fps=8, robust=True,
                   keep_bands=['B04', 'B03', 'B02'], **kwargs):
        """
        Create satellite timelapse, and export it as animated GIF file.

        Args:
            imgfile (string, optional): GIF file path.
            fps (int, optional): frames per second
            robust (bool, optional): calculate vmin and vmax from the 2nd and
                98th percentiles of the data. Defaults to True.
            keep_bands (list, optional): bands to keep (1 or 3 bands for
                gif export).

        Returns:
            Sits_ds.gif: ``IPython.display.Image`` if ``imgfile`` is None.

        Example:
            >>> geo_dc = Sits_ds(netcdf_file)
            >>> geo_dc.ds2da()
            >>> geo_dc.export2gif(imgfile='myTimeSeries.gif')
        """
        self.__ds2da(keep_bands)

        if isinstance(self.da.data, dask_array.Array):
            self.gif = geogif.dgif(self.da, fps=fps, robust=robust, **kwargs).compute()
            if imgfile:
                with open(imgfile, "wb") as f:
                    f.write(self.gif.data)
        else:
            self.gif = geogif.gif(self.da, fps=fps, robust=robust, to=imgfile, **kwargs)

