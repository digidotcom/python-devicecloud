#!/bin/bash
#
# Script that will try to test this codebase against as many
# python versions as is possible.  It does this using a combination
# of pyenv (for building various interpreters) and tox for
# testing using each of those interpreters.
#

pyversions=(2.7.16
            3.4.10
            3.5.7
            3.6.8
            3.7.3
            pypy2.7-6.0.0
            pypy3.5-6.0.0)

# first make sure that pyenv is installed
if [ ! -s "$HOME/.pyenv/bin/pyenv" ]; then
    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
fi

# Update pyenv (required for new python versions to be available)
pyenv update

# add pyenv to our path and initialize (if this has not already been done)
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"

# install each python version that we want to test with
for pyversion in ${pyversions[*]};
do
    pyenv install -s ${pyversion}
done
pyenv rehash

# This is required
pyenv global ${pyversions[*]}

# Now, run the tests after sourcing venv for tox install/use
virtualenv -q .toxenv
source .toxenv/bin/activate
pip install -q -r test-requirements.txt
tox --recreate
