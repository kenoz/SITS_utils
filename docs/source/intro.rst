Introduction
============

``sits`` is a high-level `Python package <https://github.com/kenoz/SITS_utils>`_ designed to simplify the extraction of Satellite Images Time Series (SITS) from STAC catalogs. For each specified point or polygon, it delivers image or csv files, optionally with defined dimensions (e.g., deep learning patches). The package is organized into several modules, including the core `sits` module for data extraction, an `export` module for visualization, and an `analysis` module for experimental time series forecasting. These components work together to streamline satellite data workflows and reduce the complexity of interacting with geospatial APIs.

Motivation
----------

This Python package is intended for users who want to extract satellite data without delving into the complexities of the ``pySTAC`` API and other geospatial libraries. The tool currently offers three modules:

* **Core Module** :mod:`sits` 
This is the main module for querying and downloading satellite time series. It includes the following classes:

    * :class:`sits.Csv2gdf`: Converts a CSV file containing coordinates into a GeoDataFrame.
    * :class:`sits.StacAttack`: Queries STAC catalogs to extract satellite data. It also provides utilities for applying binary masks, gap-filling missing pixels, and computing spectral indices.
    * :class:`sits.Labels`: Generates label images for training and testing purposes.
    * :class:`sits.Multiproc`: Enables multiprocessing for parallel execution of `SITS.StacAttack`.   

* **Export Module** :mod:`export`
This submodule handles NetCDF file loading and conversion to animated GIFs.

    * :class:`export.Sits_ds`: Loads a NetCDF file as an xarray.Dataset and exports it as an animated GIF.

* **Analysis Module** Module :mod:`analysis`
This experimental submodule integrates forecasting methods from the ``sktime`` package.

Limitations
-----------

- The current implementation has been developed and tested in Python 3.
- The developments are still in progress.

