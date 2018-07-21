Developer's Guide
=================

Environment Setup
-----------------

All the requirements in order to perform development on the product
should be installable in a virtualenv.

    $ pip install -r dev-requirements.txt

In order to build a release you will also need to install pandoc.  On
Ubuntu, you should be able to do:

    $ sudo apt-get install pandoc


Running the Unit Tests
----------------------

### Running Tests with Nose

Running the tests is easy with nose (included in
test-requirements.txt).  From the project root:

    $ nosetests .

To run the unit tests with coverage results (view cover/index.html),
do the following:

    $ nosetests --with-coverage --cover-html --cover-package=devicecloud .

New contributions to the library will only be accepted if they include
unit test coverage (with some exceptions).

### Testing All Versions with Tox

We also support running the tests against all supported versions of
python using a combination of
[tox](http://tox.readthedocs.org/en/latest/) and
[pyenv](https://github.com/yyuu/pyenv).  To run all of the tests
against all supported versions of python, just do the following:

    $ ./toxtest.sh

This might take awhile the first time as it will build from source a
version of the interpreter for each version supported.  If you recieve
errors from pyenv, there may be addition dependencies required.
Please visit https://github.com/yyuu/pyenv/wiki/Common-build-problems
for additional pointers.

### Running Integration and Unittests

There are some additional integration tests that run against an actual
device cloud account.  These are a bit more fragile and when something
fails, you may need to go to your device cloud account to clean things
up.

To run those tests, you can just do the following.  This script runs
the toxtest.sh script with environment variables set with your
account information.  The tests that were skipped before will now
be run with each supported version of the interpreter:

    $ ./inttest.sh

Build the Documentation
-----------------------

Documentation (outside of this file and the README) is done via
Sphinx.  To build the docs, just do the following (with virtualenv
activated):

    $ cd docs
    $ make html

The docs that are built will be located at
docs/_build/html/index.html.

The documentation for the project is published on github using a [Github
Pages](https://pages.github.com/) Project Site.  The process for
releasing a new set of documentation is the following:

1. Create a fresh clone of the project and checkout the `gh-pages`
   branch.  Although this is the same repo, the tree is completely
   separate from the main python-devicecloud codebase.
2. Remove all contents from the working area
3. From the python-devicecloud repo, `cp -r docs/_build/html/*
   /path/to/other/repo/`.
4. Commit and push the update `gh-pages` branch to github

Open Source License Header
--------------------------

Each source file should be prefixed with the following header:

    # This Source Code Form is subject to the terms of the Mozilla Public
    # License, v. 2.0. If a copy of the MPL was not distributed with this
    # file, You can obtain one at http://mozilla.org/MPL/2.0/.
    #
    # Copyright (c) 2015-2018 Digi International Inc. All rights reserved.
