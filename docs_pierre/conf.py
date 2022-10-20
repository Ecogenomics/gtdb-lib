# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys
import sphinx_rtd_theme
sys.path.append(os.path.join(os.path.dirname(__name__), '..'))
sys.path.insert(0, os.path.abspath('../gtdblib'))
sys.path.insert(0, os.path.abspath('../gtdblib/util'))



# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'GTDB Library'
copyright = '2022, Aaron,Donovan,Pierre'
author = 'Aaron,Donovan,Pierre'
release = '0.0.1'




# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_rtd_theme",
              "sphinx.ext.autodoc",
              'sphinx.ext.autosummary']

autosummary_generate = True  # Turn on sphinx.ext.autosummary

templates_path = ['_templates']
exclude_patterns = ['_build','_templates', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

