Developer's Guide
=================

Environment Setup
-----------------

All the requirements in order to perform development on the product
should be installable in a virtualenv.

    $ pip install -r test-requirements.txt

In order to build a release you will also need to install pandoc.  On
Ubuntu, you should be able to do:

    $ sudo apt-get install pandoc


Running the Unit Tests
----------------------

Running the tests is easy with nose (including in
test-requirements.txt).  From the project root:

    $ nosetests .

To run the unit tests with coverage results (view cover/index.html),
do the following:

    $ nosetests --with-coverage --cover-html --cover-package=devicecloud .

New contributions to the library will only be accepted if they include
unit test coverage (with some exceptions).


Build the Documentation
-----------------------

Documentation (outside of this file and the README) is done via
Sphinx.  To build the docs, just do the following (with virtualenv
activated):

    $ cd docs
    $ make html

The docs that are build will be located at
docs/_build/html/index.html.  Eventually, something will be rigged up
so that these get released to the web on something like
readthedocs.org.


Open Source License Header
--------------------------

Each source file should be prefixed with the following header:

    # This Source Code Form is subject to the terms of the Mozilla Public
    # License, v. 2.0. If a copy of the MPL was not distributed with this
    # file, You can obtain one at http://mozilla.org/MPL/2.0/.
    #
    # Copyright (c) 2014 Etherios, Inc. All rights reserved.
    # Etherios, Inc. is a Division of Digi International.
