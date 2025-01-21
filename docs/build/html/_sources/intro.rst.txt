Introduction
============

``SITS`` is a high-level Python package which aims to ease the extraction of Satellite Images Time Series (SITS) referenced in STAC catalogs. For each given point or polygon, it delivers image or csv files, with specified dimensions if necessary (e.g. deep learning patches). 

Motivation
**********

This Python package has been developed for those who want to extract satellite information without spending too much time to understand how to handle PyStac api and some other geospatial librairies.

This Python package has been developed for those who want to extract satellite information without spending too much time to understand how to handle pyStac api and some other geospatial librairies. Now the tool proposes 2 modules:

* The :mod:`sits` is the core module for requesting and downloading satellite time-series. It contains the following classes:
    * The :class:`SITS.Csv2gdf` allows you to convert a csv table with coordinates into a geodataframe object.
    * The :class:`SITS.StacAttack` requests STAC catalog to extract the satellite information needed.
    * The :class:`SITS.Labels` creates labels' image for training/testing.
    * The :class:`SITS.Multiproc` enables the launch of `SITS.StacAttack` in a mutiprocessing mode.   
* The :mod:`export` is a sub-module for loading netcdf file and exporting it as animated gif file. It contains the following class:
    * The :class:`export.Sits_ds` allows you to load a netcdf file as an `xarray.Dataset` and convert it as an animated gif file.

Limitations
***********

- The current implementation has been developed and tested in Python 3.
- The developments are still in progress.

