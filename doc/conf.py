# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'massa_test_framework'
copyright = '2023, Sydhds'
author = 'Sydhds'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

# Custom options

extensions.append("myst_parser")
extensions.append("sphinx.ext.autodoc")
extensions.append("sphinx.ext.napoleon")
extensions.append("sphinx_autodoc_typehints")

autodoc_mock_imports = [
    "paramiko",
    "requests",
    "tomlkit",
    "base58",
    "blake3",
    "varint",
    "ed25519",
    "betterproto",
    "grpclib",
    "patch_ng"
]

import os
import sys
sys.path.insert(0, os.path.abspath('..'))  # can import massa_test_framework (autodoc)
