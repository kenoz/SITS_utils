# Copyright (C) 2024
# author(s): Kenji OSE
# n.b. Some parts of the code (plots formatting) were kindly given by L. Dutrieux.

from matplotlib import pyplot as plt
from copy import copy
import pandas as pd
import datetime as dt
import numpy as np


class Nrt_plot():
    """Run NRT on one pixel, plot time-series and NRT outputs

    Attributes:
        proc_values (list): list of NRT instance process values
        boundary (list): list of NRT instance boundary values
        dates (list): list of monitoring dates

    Args:
        nrt_object (NRT Object): NRT instance
        array (DataArray): Vegetation Index (VI) time-series
        daterange_fit (list): start and end dates of fitting
        daterange_mon (list): start and end dates of monitoring
        vi_index (str): name of VI index
        nrt_method (str): name of NRT method
        i (int): Image column index (default is 0)
        j (int): Image raw index (default is 0)
        coords (list): coordinates in array CRS (default is None)
        ylim (list): Y cosmetic limits (default is [-1, 1])

    Returns:
        image: plot of time-series
    """

    def __init__(self, nrt_object, array, daterange_fit: list,
                 daterange_mon: list, vi_index: str, nrt_method: str,
                 i: int = 0, j: int = 0, coords: list = None,
                 ylim: list = [-1, 1], **kwargs):

        self.daterange_fit = daterange_fit
        self.daterange_mon = daterange_mon
        self.vi_index = vi_index
        self.nrt_method = nrt_method
        self.break_dt = 0
        self.ylim = ylim
        self.nrt_object = copy(nrt_object)
        # test on coordinates types (ij vs crs)
        if coords is not None:
            self.array = array.sel(x=[coords[0]], y=[coords[1]],
                                   method='nearest')
        else:
            self.array = array.isel(x=[i], y=[j])
        # arrays for fitting and monitoring periods
        self.array_history = self.array.sel(time=slice(min(self.daterange_fit),
                                                       max(self.daterange_fit)
                                                      ))
        self.array_monitor = self.array.sel(time=slice(min(self.daterange_mon),
                                                       max(self.daterange_mon)
                                                      ))

        self.nrt_object.fit(dataarray=self.array_history, **kwargs)

        self.proc_values = list()
        self.boundary = list()
        self.dates = self.array_monitor.time.values.astype('M8[s]').astype(dt.datetime)
        for array, date in zip(self.array_monitor.values, self.dates):
            self.nrt_object.monitor(array=array, date=date)
            self.proc_values.append(self.nrt_object.process[0, 0])
            if isinstance(self.nrt_object.boundary, int):
                self.boundary.append(self.nrt_object.boundary)
            else:
                self.boundary.append(self.nrt_object.boundary[0, 0])
        self.__plot_config()

    def plot_predict(self, freq='5D'):
        """Plot predicted time-series

        Args:
            freq (str): key value for calendar frequency (default is '5D')

        Returns:
            void
        """
        date_index = pd.date_range(start=min(self.daterange_fit),
                                   end=max(self.daterange_mon),
                                   freq=freq)
        self.date_list = date_index.to_list()
        self.pred_values = [self.nrt_object.predict(d)[0, 0] for d in self.date_list]
        self.ax0.plot(self.date_list, self.pred_values,
                      label='Predicted values')
        handles0, labels0 = self.ax0.get_legend_handles_labels()
        self.ax1.legend(handles0, labels0, loc='upper left')

    def plot_model(self, color_p='orange', color_b='black'):
        """Plot model's process and boundary values

        Args:
            color_p (str): line color of process values (default is 'orange')
            color_b (str): line color of boudary values (default is 'black')

        Returns:
            void
        """

        self.ax1.plot(self.dates, self.proc_values, color=color_p,
                      label=f'{self.nrt_method} process value')
        self.ax1.plot(self.dates, self.boundary, color=color_b,
                      linestyle='dashed', label='Control limits')
        self.ax1.plot(self.dates, -np.array(self.boundary), color=color_b,
                      linestyle='dashed')

    def plot_break(self, color_break='magenta'):
        """Plot break line if exists

        Args:
            color_break (str): line color of break (default is 'magenta')

        Returns:
            void
        """
        if self.nrt_object.mask[0, 0] == 3:
            self.break_dt = self.nrt_object.detection_date[0, 0]
            break_dt = dt.datetime(1970, 1, 1) + dt.timedelta(days=int(self.break_dt))
            self.ax0.vlines(x=break_dt, ymin=self.ylim[0], ymax=self.ylim[1],
                            color=color_break)

    def plot_date(self, mon_date, style='dotted', color='magenta'):
        mon_dt = dt.datetime(1970, 1, 1) + dt.timedelta(days=int(mon_date))
        self.ax0.vlines(x=mon_dt, ymin=self.ylim[0], ymax=self.ylim[1],
                        linestyles=style, color=color)

    def __plot_config(self):
        """Plot canvas configuration
        """
        self.fig, [self.ax0, self.ax1] = plt.subplots(2, 1, sharex=True)
        # Set x-axis limits to the entire date range
        self.ax0.set_xlim(min(self.daterange_fit), max(self.daterange_mon))
        self.ax0.set_ylim(self.ylim)
        self.ax0.axvspan(min(self.daterange_fit), max(self.daterange_fit),
                         color='dimgray', alpha=0.5)
        self.ax0.axvspan(min(self.daterange_mon), max(self.daterange_mon),
                         color='lightgray', alpha=0.5)

        self.ax1.tick_params(axis='x', labelrotation=45)
        self.ax0.set_ylabel(self.vi_index)
        self.ax1.set_ylabel(self.nrt_method)

        self.ax0.grid(True, color='black', linestyle='--')
        self.ax1.grid(True, linestyle='--')

        self.ax0.plot(self.array_history["time"].values,
                      self.array_history.squeeze().values,
                      marker='.', color='green', linestyle='None')
        self.ax0.plot(self.array_monitor["time"].values,
                      self.array_monitor.squeeze().values,
                      marker='.', color='black', linestyle='None')

    def __legend(self):
        """Add legend to plot
        """
        self.ax1.legend(loc='upper left')
        # Add ax0's legend elements to ax1's legend
        self.handles0, self.labels0 = self.ax0.get_legend_handles_labels()
        self.ax1.legend(handles=self.ax1.get_legend_handles_labels()[0] + self.handles0,
                        labels=self.ax1.get_legend_handles_labels()[1] + self.labels0,
                        loc='upper left')

    def show(self):
        """Show plot
        """
        self.__legend()
        plt.tight_layout()
        plt.show()

    def savefig(self, outpath):
        """Save plot as file

        Args:
            outpath (str): output image filepath
        """
        self.__legend()
        plt.tight_layout()
        plt.savefig(outpath)