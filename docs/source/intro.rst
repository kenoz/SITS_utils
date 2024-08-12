Introduction
============

``SITS`` is a high-level Python package which aims to ease the extraction of Satellite Images Time Series (SITS) referenced in STAC catalogs. For each given point or polygon, it delivers image or csv files, with specified dimensions if necessary (e.g. deep learning patches). 

Motivation
**********

This Python package has been developed for those who want to extract satellite information without spending too much time to understand how to handle PyStac api and some other geospatial librairies.
- The :class:`SITS.Csv2gdf` allows you to convert a csv table with coordinates into a geodataframe object.
- The :class:`SITS.StacAttack` requests STAC catalog to extract the satellite information needed.

Limitations
***********

- The current implementation has been developed and tested in Python 3.
- The developments are still in progress.

