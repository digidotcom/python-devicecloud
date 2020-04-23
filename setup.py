# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015-2018 Digi International Inc.

import re
import os
from setuptools import setup, find_packages

VERSIONFILE = "devicecloud/version.py"

def get_version():
    # In order to get the version safely, we read the version.py file
    # as text.  This is necessary as devicecloud/__init__.py uses
    # things that won't yet be present when the package is being
    # installed.
    verstrline = open(VERSIONFILE, "r").read()
    version_string_re = re.compile(r"^__version__ = ['\"]([^'\"]*)['\"]", re.MULTILINE)
    match = version_string_re.search(verstrline)
    if match:
        return match.group(1)
    else:
        raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


def get_long_description():
    long_description = open('README.md').read()
    try:
        import subprocess
        import pandoc
        doc = pandoc.Document()
        doc.markdown = long_description.encode('utf-8')
        open("README.rst", "wb").write(doc.rst)
    except:
        print("Could not find pandoc or convert properly")
        print("  make sure you have pandoc (system) and pyandoc (python module) installed")

    return long_description

setup(
    name="devicecloud",
    version=get_version(),
    description="Python API to the Digi Device Cloud",
    long_description_content_type='text/markdown',
    long_description=get_long_description(),
    url="https://github.com/digidotcom/python-devicecloud",
    author="Digi International Inc.",
    author_email="brandon.moser@digi.com",
    packages=find_packages(),
    install_requires=open('requirements.txt').read().split(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries",
        "Operating System :: OS Independent",
    ],
)
