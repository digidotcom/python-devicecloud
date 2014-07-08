#!/bin/bash
#
# Script that will try to test this codebase against as many
# python versions as is possible.  It does this using a combination
# of pythonbrew (for building various interpreters) and tox for
# testing using each of those interpreters.
#

pyversions=(2.6.7
            2.7.7
            3.2.5
            3.3.5
            3.4.1)

# first make sure that pythonbrew is installed
if [ ! -s "$HOME/.pythonbrew/etc/bashrc" ]; then
  curl -kLO http://github.com/utahta/pythonbrew/raw/master/pythonbrew-install
  chmod +x pythonbrew-install
  ./pythonbrew-install
  rm ./pythonbrew-install
fi

# add pythonbrew into our environment
source "$HOME/.pythonbrew/etc/bashrc"

# install each python version that we want to test with
for pyversion in ${pyversions[*]};
do
  if [ ! -s "$HOME/.pythonbrew/bin/py${pyversion}" ]; then
    pythonbrew install ${pyversion}
  fi
done

# Now, run the tests after sourcing venv for tox install/use
pythonbrew symlink
pythonbrew venv -p 2.7.7 create python-devicecloud-tox
pythonbrew venv use python-devicecloud-tox
pip install -q -r test-requirements.txt
tox
