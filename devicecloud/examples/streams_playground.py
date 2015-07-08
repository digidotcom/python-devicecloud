# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
from math import pi
import pprint
import time

from devicecloud.examples.example_helpers import get_authenticated_dc

from devicecloud.streams import DataPoint, NoSuchStreamException, STREAM_TYPE_INTEGER, STREAM_TYPE_JSON


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
            data=i * pi,
            description="This is {} * pi".format(i)
        ))

    for i, stream in enumerate(test_stream.read()):
        print ("{}, {!r}".format(i + 1, stream))

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


def write_points_and_delete_some(dc):
    test_stream = dc.streams.get_stream_if_exists("test")

    if test_stream is not None:
        test_stream.delete()

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

    print("Writing data points with five second delay")
    for i in range(5):
        print("Writing point {} / 5".format(i + 1))
        test_stream.write(DataPoint(
            data=i * 1000,
            description="This is {} * pi".format(i)
        ))
        if i < (5 - 1):
            time.sleep(1)

    points = list(test_stream.read(newest_first=False))
    print("Read {} data points, removing the first".format(len(points)))

    # Remove the first
    test_stream.delete_datapoint(points[0])
    points = list(test_stream.read(newest_first=False))
    print("Read {} data points, removing ones written in last 30 seconds".format(len(points)))

    # delete the ones in the middle
    test_stream.delete_datapoints_in_time_range(
        start_dt=points[1].get_timestamp(),
        end_dt=points[-1].get_timestamp()
    )
    points = list(test_stream.read(newest_first=False))
    print("Read {} data points.  Will try to delete all next".format(len(points)))
    pprint.pprint(points)

    # let's try without any range at all and see if they all get deleted
    test_stream.delete_datapoints_in_time_range()
    points = list(test_stream.read(newest_first=False))
    print("Read {} data points".format(len(points)))

    test_stream.delete()


def bulk_write_datapoints_single_stream(dc):
    datapoints = []
    for i in range(300):
        datapoints.append(DataPoint(
            data_type=STREAM_TYPE_INTEGER,
            units="meters",
            data=i,
        ))

    stream = dc.streams.get_stream("my/test/bulkstream")
    stream.bulk_write_datapoints(datapoints)
    print("---" + stream.get_stream_id() + "---")
    print(" ".join(str(dp.get_data()) for dp in stream.read(newest_first=False)))
    print("")
    stream.delete()


def bulk_write_datapoints_multiple_streams(dc):
    datapoints = []
    for i in range(300):
        datapoints.append(DataPoint(
            stream_id="my/stream%d" % (i % 3),
            data_type=STREAM_TYPE_INTEGER,
            units="meters",
            data=i,
        ))
    dc.streams.bulk_write_datapoints(datapoints)

    for stream in dc.streams.get_streams():
        if stream.get_stream_id().startswith('my/stream'):
            print("---" + stream.get_stream_id() + "---")
            print(" ".join(str(dp.get_data()) for dp in stream.read(newest_first=False)))
            print("")
        stream.delete()


def create_and_use_json_stream(dc):
    # get a test stream reference
    test_stream = dc.streams.get_stream_if_exists("test-json")

    # we want a clean stream to work with.  If the stream exists, nuke it
    if test_stream is not None:
        test_stream.delete()

    test_stream = dc.streams.create_stream(
        stream_id="test-json",
        data_type=STREAM_TYPE_JSON,
        description='a stream used for testing json',
        units='international json standard unit (IJSU)',
    )

    test_stream.write(DataPoint(
            data_type=STREAM_TYPE_JSON,
            data = {'key1': 'value1',
                    2: 2,
                    'key3': [1, 2, 3]},
            description="Some JSON data in IJSUs",
        )
    )

    time.sleep(5)

    print(test_stream.get_current_value())

    test_stream.delete()

if __name__ == '__main__':
    dc = get_authenticated_dc()
    create_and_use_json_stream(dc)
    create_stream_and_delete(dc)
    attempt_to_delete_non_existant(dc)
    write_points_and_delete_some(dc)
    bulk_write_datapoints_single_stream(dc)
    bulk_write_datapoints_multiple_streams(dc)

