=============
 PyBitbucket
=============

A Python wrapper for the Bitbucket API.

----------
Developing
----------

Python Virtual Environment Setup (for OS X)
===========================================

It's not virtual like a virtual machine. More like a specialized container for a Python version and libraries.

1. `brew install python` This installs the latest version of Python 2.7 with a version of setuptools and pip. Unfortunately, those versions of setuptools and pip seem to be broken.
2. `pip install --upgrade --no-use-wheel setuptools`
3. `pip install --upgrade --no-use-wheel pip`
4. `pip install virtualenvwrapper`

Project Setup
=============

1. Clone the repository and set it as the current working directory.
2. *(Optional, but good practice)* Create a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/): `mkvirtualenv python-bitbucket` Once created, use `workon python-bitbucket` to restore the virtual environment.
3. `pip install -r requirements-dev.txt` Loads required libraries into the virtual environment.
5. `paver test_all` Run all the unit tests and analyze the source code.
