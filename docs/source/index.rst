.. sits documentation master file, created by
   sphinx-quickstart on Mon Aug  5 09:54:12 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: https://img.shields.io/badge/GitHub-Repo-blue?logo=github
   :target: https://github.com/kenoz/SITS_utils
   :alt: GitHub Repository


Welcome to sits's documentation!
================================

``sits`` is a high-level Python package designed to simplify the extraction and processing of Satellite Image Time Series (SITS) referenced in STAC catalogs. For any given point or polygon, it efficiently handles data retrieval and, leveraging ``spyndex``, can calculate a wide array of spectral indices. The processed results can be exported in various formats, including image files, CSV tables, or dynamic animated GIFs, with customizable dimensions suitable for applications such as deep learning.
In addition to its core functionalities, the package includes an experimental analysis module that integrates forecasting methods from the ``sktime`` library. This module enables users to apply time series models to satellite-derived data, opening possibilities for predictive analytics and temporal pattern exploration.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   intro
   sits
   export
   analysis
   tutorials

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
