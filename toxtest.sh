#!/bin/bash
#
# Script that will try to test this codebase against as many
# python versions as is possible.  It does this using a combination
# of pyenv (for building various interpreters) and tox for
# testing using each of those interpreters.
#

pyversions=(2.7.7
            3.3.5
            3.4.3
            3.5.5
            3.6.6
            3.7.0
            pypy-2.3.1)

# first make sure that pyenv is installed
if [ ! -s "$HOME/.pyenv/bin/pyenv" ]; then
    curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
fi

# Update pyenv (required for new python versions to be available)
(cd $HOME/.pyenv && git pull)

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
