@echo off

rem Install/Upgrade Build Tools and Dependencies
pip install --upgrade setuptools wheel
pip install --upgrade twine

rem Build distribution
python setup.py sdist bdist_wheel

rem Upload to public Pypi Server
python -m twine upload dist/*

rem Upload to Internal Pypi Server
python setup.py sdist upload -i http://pypi.digi.com/simple

rem "Package uploaded to Pypi Servers"
