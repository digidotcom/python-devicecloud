import re
import os
from setuptools import setup, find_packages


def get_version():
    # In order to get the version safely, we read the version.py file
    # as text.  This is necessary as devicecloud/__init__.py uses
    # things that won't yet be present when the package is being
    # installed.
    verstrline = open("devicecloud/version.py", "r").read()
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

        process = subprocess.Popen(
            ['which pandoc'],
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True)

        pandoc_path = process.communicate()[0]
        pandoc_path = pandoc_path.strip('\n')

        pandoc.core.PANDOC_PATH = pandoc_path

        doc = pandoc.Document()
        doc.markdown = long_description
        long_description = doc.rst
        open("README.rst", "w").write(doc.rst)
    except:
        if os.path.exists("README.rst"):
            long_description = open("README.rst").read()
        else:
            print("Could not find pandoc or convert properly")
            print("  make sure you have pandoc (system) and pyandoc (python module) installed")

    return long_description


setup(
    name="devicecloud",
    version=get_version(),
    description="Python API to the Digi Device Cloud",
    long_description=get_long_description(),
    url="https://github.com/digidotcom/python-devicecloud",
    author="Digi International, Inc.",
    author_email="paul.osborne@digi.com",
    packages=find_packages(),
    install_requires=open('requirements.txt').read().split(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Software Development :: Libraries",
        "Operating System :: OS Independent",
    ],
)
