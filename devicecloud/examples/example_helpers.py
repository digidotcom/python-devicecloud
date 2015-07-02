# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
from getpass import getpass
import os
from six.moves import input
from devicecloud import DeviceCloud


def get_authenticated_dc():
    while True:
        base_url = os.environ.get('DC_BASE_URL', 'https://login.etherios.com')

        username = os.environ.get('DC_USERNAME', None)
        if not username:
            username = input("username: ")

        password = os.environ.get('DC_PASSWORD', None)
        if not password:
            password = getpass("password: ")

        dc = DeviceCloud(username, password, base_url=base_url)
        if dc.has_valid_credentials():
            print("Credentials accepted!")
            return dc
        else:
            print("Invalid username or password provided, try again")
