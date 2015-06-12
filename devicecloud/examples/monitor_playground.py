# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2015, Digi International, Inc..
from getpass import getpass
import pprint
import random
import time

from devicecloud import DeviceCloud
from devicecloud.filedata import fd_name, fd_size, fd_type, fd_path
from devicecloud.streams import DataPoint
import six
from six.moves import input

def get_authenticated_dc():
    while True:
        user = input("username: ")
        password = getpass("password: ")
        dc = DeviceCloud(user, password, base_url="https://login.etherios.com")
        if dc.has_valid_credentials():
            print("Credentials accepted!")
            return dc
        else:
            print("Invalid username or password provided, try again")


if __name__ == '__main__':
    dc = get_authenticated_dc()

    # Create a fresh monitor over a pretty broad set of topics
    topics = ['DeviceCore', 'FileDataCore', 'FileData', 'DataPoint']
    mon = dc.monitor.get_monitor(topics)
    if mon is not None:
        mon.delete()
    mon = dc.monitor.create_monitor(topics)

    def listener(data):
        pprint.pprint(data)
        return True  # we got it!

    mon.add_listener(listener)

    test_stream = dc.streams.get_stream("test")
    try:
        while True:
            test_stream.write(DataPoint(random.random()))
            time.sleep(3.14)
    except KeyboardInterrupt:
        print("Shutting down threads...")

    dc.monitor.stop_listeners()
