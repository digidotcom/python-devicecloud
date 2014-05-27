import devicecloud
from setuptools import setup, find_packages


def get_long_description():
    try:
        return open("README.rst").read()
    except IOError:
        print("README.rst not found, may need to run pandoc on README.md")
        return ""


setup(
    name="devicecloud",
    version=devicecloud.__version__,
    description="Python API to the Device Cloud by Etherios",
    long_description=get_long_description(),
    url="https://github.com/etherios/python-devicecloud",
    author="Stephen Stack",
    author_email="stephen.stack@etherios.com",
    packages=find_packages(),
    install_requires=open('requirements.txt').read().split(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 2.4",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries",
        "Operating System :: OS Independent",
  ],
)
