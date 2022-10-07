import os
import sys
from datetime import datetime
import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath('../..'))
from gtdblib import __author__, __version__, __title__, __url__

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# The full version, including alpha/beta/rc tags
release = __version__
project = __title__
copyright = f'{datetime.now().year}, {__author__}'
author = __author__

# The full version, including alpha/beta/rc tags
version = __version__

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

github_url = __url__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx_rtd_theme', "sphinx.ext.autodoc", "sphinx.ext.autosummary", "sphinx_autodoc_typehints"]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"

html_static_path = ['_static']
