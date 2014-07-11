# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.
from getpass import getpass
from math import pi

from devicecloud import DeviceCloud
from devicecloud.streams import DataPoint, NoSuchStreamException


def get_authenticated_dc():
    while True:
        user = raw_input("username: ")
        password = getpass("password: ")
        dc = DeviceCloud(user, password)
        if dc.has_valid_credentials():
            print ("Credentials accepted!")
            return dc
        else:
            print ("Invalid username or password provided, try again")


def create_stream_and_delete(dc):
    # get a test stream reference
    test_stream = dc.streams.get_stream_if_exists("test")

    # we want a clean stream to work with.  If the stream exists, nuke it
    if test_stream is not None:
        test_stream.delete()

    test_stream = dc.streams.create_stream(
        stream_id="test",
        data_type='float',
        description='a stream used for testing',
        units='some-unit',
    )

    for i in range(5):
        test_stream.write(DataPoint(
            data=i * pi
        ))

    raw_input("We wrote some points to the cloud, go check it out!")

    # now cleanup by deleting the stream
    test_stream.delete()


def attempt_to_delete_non_existant(dc):
    try:
        dc.streams.get_stream("a/nonexistant/stream").delete()
    except NoSuchStreamException:
        print ("The stream that doesn't exist could not be deleted "
               "because it does not exist!")
    else:
        print ("!!! We were able to delete something which does not exist!!!")


if __name__ == '__main__':
    dc = get_authenticated_dc()
    create_stream_and_delete(dc)
    attempt_to_delete_non_existant(dc)
