#!/bin/bash
#
# This script will run all unit and integration
# tests.  In order to run the integration tests, we
# need to get a username and password, which is what
# this script does.  The rest of the work is done
# by the 'toxtest.sh' script
#

export RUN_INTEGRATION_TESTS=yes
if [ -z $DC_USERNAME ]; then
    echo -n 'username: '
    read username
    export DC_USERNAME="$username"
fi

if [ -z $DC_PASSWORD ]; then
    echo -n 'password: '
    read -s password
    export DC_PASSWORD="$password"
fi

./toxtest.sh
