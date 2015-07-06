# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2015, Digi International, Inc..
import pprint
import random
import time

from devicecloud.examples.example_helpers import get_authenticated_dc

from devicecloud.streams import DataPoint

def test_tcp_monitor(dc):
    # Create a fresh monitor over a pretty broad set of topics
    topics = ['DeviceCore', 'FileDataCore', 'FileData', 'DataPoint']
    mon = dc.monitor.get_monitor(topics)
    if mon is not None:
        mon.delete()
    mon = dc.monitor.create_tcp_monitor(topics)
    pprint.pprint(mon.get_metadata())

    def listener(data):
        pprint.pprint(data)
        return True  # we got it!

    mon.add_callback(listener)

    test_stream = dc.streams.get_stream("test")
    try:
        while True:
            test_stream.write(DataPoint(random.random()))
            time.sleep(3.14)
    except KeyboardInterrupt:
        print("Shutting down threads...")

    dc.monitor.stop_listeners()

def test_http_monitor(dc):
    # Create a fresh monitor over a pretty broad set of topics
    topics = ['DeviceCore', 'FileDataCore', 'FileData', 'DataPoint']
    mon = dc.monitor.get_monitor(topics)
    if mon is not None:
        mon.delete()
    mon = dc.monitor.create_http_monitor(topics, 'http://digi.com',  transport_token=None, transport_method='PUT',
                                         connect_timeout=0, response_timeout=0, batch_size=1, batch_duration=0,
                                         compression='none', format_type='json')
    pprint.pprint(mon.get_metadata())

    def listener(data):
        pprint.pprint(data)
        return True  # we got it!

    test_stream = dc.streams.get_stream("test")
    try:
        while True:
            test_stream.write(DataPoint(random.random()))
            time.sleep(3.14)
    except KeyboardInterrupt:
        print("Shutting down threads...")

if __name__ == '__main__':
    dc = get_authenticated_dc()
    test_http_monitor(dc)

