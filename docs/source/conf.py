# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path

# Path to the 'source' directory (where conf.py is)
docs_source_dir = Path(__file__).parent
# Go up one level to 'docs'
docs_dir = docs_source_dir.parent
# Go up one more level to 'your_project_root/'
project_root = docs_dir.parent

# Add the project root to sys.path
sys.path.insert(0, str(project_root))
#sys.path.insert(0, os.path.abspath('../../sits/'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'sits'
copyright = '%Y, Kenji Ose'
author = 'Kenji Ose'
release = '0.6.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.napoleon',
              'sphinx.ext.autodoc',
              'sphinx.ext.autosummary',]

templates_path = ['_templates']
exclude_patterns = ['_build',
                    'Thumbs.db',
                    '.DS_Store',
                    '**.ipynb_checkpoints'
                   ]

autodoc_default_options = {
    'members': True,
    'undoc-members': True, # Good for debugging, remove later if you don't want undoc members
    'private-members': False,
    'special-members': '__init__',
    'show-inheritance': True,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
