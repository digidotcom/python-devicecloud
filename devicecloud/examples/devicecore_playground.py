# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.
from getpass import getpass

from devicecloud import DeviceCloud
from devicecloud.devicecore import dev_mac


def get_authenticated_dc():
    while True:
        user = raw_input("username: ")
        password = getpass("password: ")
        dc = DeviceCloud(user, password,
                         base_url="https://test-idigi-com-2v5p9uat81qu.runscope.net")
        if dc.has_valid_credentials():
            print ("Credentials accepted!")
            return dc
        else:
            print ("Invalid username or password provided, try again")


if __name__ == '__main__':
    dc = get_authenticated_dc()
    devices = dc.devicecore.get_devices(
        (dev_mac == '00:40:9D:50:B0:EA')
    )
    for dev in devices:
        print(dev)
