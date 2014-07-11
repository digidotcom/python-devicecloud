#!/bin/bash
#
# Script that will try to test this codebase against as many
# python versions as is possible.  It does this using a combination
# of pyenv (for building various interpreters) and tox for
# testing using each of those interpreters.
#

pyversions=(2.7.7
            3.2.5
            3.3.5
            3.4.1) # 2.6.9 (not supported)

# first make sure that pyenv is installed
if [ ! -s "$HOME/.pyenv/bin/pyenv" ]; then
    curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
fi

# add pyenv to our path and initialize (if this has not already been done)
export PATH="$HOME/.pyenv/shims:$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"

# install each python version that we want to test with
for pyversion in ${pyversions[*]};
do
    echo "Ensuring Python ${pyversion} is installed"
    pyenv install -s ${pyversion}
done
pyenv rehash

# This is required
pyenv global "${pyversions}"

# Now, run the tests after sourcing venv for tox install/use
if [ ! -d ".toxenv" ]
then
    virtualenv-2.7 .toxenv
fi
source .toxenv/bin/activate

pip install -q -r test-requirements.txt
tox
