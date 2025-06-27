# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

#import sits

# Add the project root to sys.path
#sys.path.insert(0, os.path.join(str(project_root), 'sits'))
sys.path.insert(0, os.path.abspath('../..'))

project_root = os.path.abspath('../..')

# --- DEBUGGING PRINTS (TEMPORARY - REMOVE BEFORE COMMITING) ---
print(f"--- DEBUG CONF.PY START ---")
print(f"Current Working Directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")
print(f"Project Root Added to Path: {project_root}")
try:
    # Try to import your top-level package
    import sits
    print(f"Successfully imported top-level 'sits' package in conf.py!")
    # Then try to import the specific module that was failing
    import sits.sits # This is the module that contains def_geobox etc.
    print(f"Successfully imported 'sits.sits' module in conf.py!")
except Exception as e:
    print(f"FAILED to import 'sits' or 'sits.sits' in conf.py: {e}")
    import traceback
    traceback.print_exc(file=sys.stdout)
print(f"--- DEBUG CONF.PY END ---")
# --- END DEBUGGING ---

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'sits'
copyright = '%Y, Kenji Ose'
author = 'Kenji Ose'
release = '0.6.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx.ext.autosummary',]

templates_path = ['_templates']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
