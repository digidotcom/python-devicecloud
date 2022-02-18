#!/bin/sh

# Install/Upgrade Build Tools and Dependencies
python -m pip install --upgrade setuptools wheel
python -m pip install --upgrade twine

# Build distribution
python setup.py sdist bdist_wheel

# Upload to public Pypi Server
python -m twine upload dist/*

# Upload to Internal Pypi Server
python setup.py sdist upload -i http://pypi.digi.com/simple

echo "Package uploaded to Pypi Servers"

