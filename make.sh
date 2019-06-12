#!/bin/sh

# Install/Upgrade Build Tools and Dependencies
pip install --upgrade setuptools wheel
pip install --upgrade twine

# Build distribution
python setup.py sdist bdist_wheel

# Upload to public Pypi Server
python -m twine upload dist/*

echo "Package uploaded to Pypi"
