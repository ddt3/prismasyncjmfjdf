# PRISMAsync Python module
This repository contains a Python module for communication with PRISMAsync. It needs to be installed locally by using:

     pip install https://github.com/ddt3/prismasyncjmfjdf/releases/latest/download/prismasyncjmfjdf.tar.gz
# Contents of this module
For details on the contents of this module:

    python -m pydoc prismasyncjmfjdf
    or to create a html page:
    python -m pydoc -w prismasyncjmfjdf
# Building a new version
Make sure build and setuptools are installed:

    python -m pip install build setuptools

In the folder where ``pyproject.toml`` can be found, start build:

    python -m build .

