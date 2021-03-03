# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import shutil

# sys.path.insert(0, os.path.abspath('.'))
import sphinx.ext.apidoc
from pkg_resources import get_distribution
from setuptools import find_packages

# -- Project information -----------------------------------------------------

project = 'barcode-reader'
copyright = '2021, Antoine Humbert'
author = 'Antoine Humbert'

# The full version, including alpha/beta/rc tags
release = get_distribution(project).version
version = '.'.join(release.split('.')[:2])


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]


def setup(app):
    source_dir = os.path.dirname(__file__)
    api_dir = os.path.join(source_dir, 'api')
    shutil.rmtree(api_dir, ignore_errors=True)
    projects_sources_dir = os.path.normpath(os.path.join(source_dir, '..', '..', 'src'))
    for package_name in find_packages(projects_sources_dir):
        sphinx.ext.apidoc.main(
            ['--implicit-namespaces', '-f', '-e', '-o', api_dir, os.path.join(projects_sources_dir, package_name)]
        )


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}
