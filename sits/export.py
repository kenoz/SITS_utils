import xarray as xr
import dask.array as dask_array
import geogif
import pandas as pd
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.cm as cm
from importlib.resources import files
#import os


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

    def __add_watermark(self, frame: np.ndarray, text: str,
                        position='bottom right',
                        font_size=40, color=(255, 255, 255),
                        opacity=128):
        """
        Adds a semi-transparent text watermark to a NumPy RGB image using Pillow.

        Parameters:
            frame (np.ndarray): RGB image of shape (H, W, 3), dtype=uint8
            text (str): Watermark text
            position (str): One of 'top left', 'top right', 'bottom left', 'bottom right'
            font_size (int): Font size in points
            color (tuple): RGB color of the text
            opacity (int): 0–255 transparency level

        Returns:
            np.ndarray: Watermarked image as uint8 RGB array
        """
        img = Image.fromarray(frame).convert("RGBA")
        txt_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)

        try:
            font_path = files("sits.fonts").joinpath("NotoSans-Regular.ttf")
            font = ImageFont.truetype(str(font_path), font_size)
        except IOError:
            font = ImageFont.load_default()

        text_size = draw.textbbox((0, 0), text, font=font)
        text_width = text_size[2] - text_size[0]
        text_height = text_size[3] - text_size[1]

        margin = 10
        positions = {
            'top left': (margin, margin),
            'top right': (img.width - text_width - margin, margin),
            'bottom left': (margin, img.height - text_height - margin),
            'bottom right': (img.width - text_width - margin, img.height - text_height - margin),
        }
        xy = positions.get(position, positions['bottom right'])

        draw.text(xy, text, font=font, fill=color + (opacity,))
        watermarked = Image.alpha_composite(img, txt_layer).convert("RGB")
        return np.array(watermarked, dtype=np.uint8)

    def __pad_to_square(self, frame: np.ndarray, fill_color=(0, 0, 0)):
        """to fill
        """
        img = Image.fromarray(frame)
        w, h = img.size
        scale = 1080 / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.BICUBIC)

        # Create 1080x1080 canvas
        canvas = Image.new("RGB", (1080, 1080), fill_color)
        offset = ((1080 - new_w) // 2, (1080 - new_h) // 2)
        canvas.paste(img, offset)
        return np.array(canvas)

    def export2vid_old(self, output_path: str,
                   keep_bands: list,
                   fps: int = 10, rgb_indices=(0, 1, 2),
                   vmin=None, vmax=None,
                   square=False,
                   watermark_text=None,
                   watermark_loc='bottom right',
                   watermark_param=None,
                   square_param=None):
        """to fill
        """

        self.__ds2da(keep_bands)

        assert self.da.ndim == 4 and self.da.shape[1] >= 3, "Expected shape (time, bands, y, x)"

        with imageio.get_writer(output_path, fps=fps) as writer:
            for t in range(self.da.sizes['time']):
                rgb = self.da.isel(time=t).values[rgb_indices, :, :]
                rgb = np.transpose(rgb, (1, 2, 0))  # (y, x, 3)

                if vmin is None:
                    vmin = rgb.min()
                if vmax is None:
                    vmax = rgb.max()

                rgb = np.clip((rgb - vmin) / (vmax - vmin), 0, 1)
                rgb = (rgb * 255).astype(np.uint8)

                if square:
                    square_param = square_param or {}
                    rgb = self.__pad_to_square(rgb, fill_color=(0, 0, 0),
                                               **square_param)

                if watermark_text:
                    watermark_param = watermark_param or {}
                    rgb = self.__add_watermark(rgb,
                                               text=watermark_text,
                                               position=watermark_loc,
                                               **watermark_param)

                writer.append_data(rgb)

    def export2vid(self, output_path: str,
                   keep_bands: list,
                   fps: int = 10,
                   #rgb_indices=(0, 1, 2),
                   colormap: str = "viridis",
                   vmin=None, vmax=None,
                   square=False,
                   watermark_text=None,
                   watermark_loc='bottom right',
                   watermark_param=None,
                   square_param=None):
        """Export EO time series to video, supporting RGB and monoband with colormap.
        """

        self.__ds2da(keep_bands)
        #assert self.da.ndim == 4, "Expected shape (time, bands, y, x)"

        mono_mode = self.da.shape[1] == 1

        with imageio.get_writer(output_path, fps=fps) as writer:
            for t in range(self.da.sizes['time']):
                arr = self.da.isel(time=t).values  # shape: (bands, y, x)

                if mono_mode:
                    band = arr[0, :, :]
                    if vmin is None: vmin = band.min()
                    if vmax is None: vmax = band.max()
                    norm = np.clip((band - vmin) / (vmax - vmin), 0, 1)
                    cmap = cm.get_cmap(colormap)
                    rgb = (cmap(norm)[:, :, :3] * 255).astype(np.uint8)  # drop alpha
                else:
                    #rgb = arr[rgb_indices, :, :]
                    rgb = arr[(0, 1, 2), :, :]
                    rgb = np.transpose(rgb, (1, 2, 0))  # (y, x, 3)
                    if vmin is None: vmin = rgb.min()
                    if vmax is None: vmax = rgb.max()
                    rgb = np.clip((rgb - vmin) / (vmax - vmin), 0, 1)
                    rgb = (rgb * 255).astype(np.uint8)

                if square:
                    square_param = square_param or {}
                    rgb = self.__pad_to_square(rgb, fill_color=(0, 0, 0), **square_param)

                if watermark_text:
                    watermark_param = watermark_param or {}
                    rgb = self.__add_watermark(rgb,
                                               text=watermark_text,
                                               position=watermark_loc,
                                               **watermark_param)

                writer.append_data(rgb)

