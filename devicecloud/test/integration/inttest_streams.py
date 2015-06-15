# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

"""Integration tests for streams functionality

These tests test that the streams functionality actually works against the device
cloud itself.

"""
from math import pi
import datetime

from devicecloud.streams import DataPoint, STREAM_TYPE_INTEGER
from devicecloud.test.integration.inttest_utilities import DeviceCloudIntegrationTestCase, dc_inttest_main
import six


class StreamsIntegrationTestCase(DeviceCloudIntegrationTestCase):

    def test_basic_nonbulk_stream_operations(self):
        #
        # This test verifiest that we can perform a number of simple operations on
        # a data stream (non-bulk).  The ops are create, write, read, and delete
        #
        SID = "pythondc-inttest/test_basic_nonbulk_stream_operations"

        # get a test stream reference
        test_stream = self._dc.streams.get_stream_if_exists(SID)

        # we want a clean stream to work with.  If the stream exists, nuke it
        if test_stream is not None:
            test_stream.delete()

        test_stream = self._dc.streams.create_stream(
            stream_id=SID,
            data_type='float',
            description='a stream used for testing',
            units='some-unit',
        )

        for i in range(5):
            test_stream.write(DataPoint(
                data=i * pi,
                description="This is {} * pi".format(i)
            ))

        for i, dp in enumerate(test_stream.read(newest_first=False)):
            self.assertAlmostEqual(dp.get_data(), i * pi)

        # now cleanup by deleting the stream
        test_stream.delete()

    def test_bulk_write_datapoints_multiple_streams(self):
        #
        # This test verifies that we can write in bulk a bunch of datapoints to several
        # datastreams and read them back.
        #
        SID_FMT = "pythondc-inttest/test_bulk_write_datapoints_multiple_streams-{}"
        datapoints = []
        dt = datetime.datetime.now()
        for i in range(300):
            datapoints.append(DataPoint(
                stream_id=SID_FMT.format(i % 3),
                data_type=STREAM_TYPE_INTEGER,
                units="meters",
                timestamp=dt - datetime.timedelta(seconds=300 - i),
                data=i,
            ))

        # remove any existing data before starting out
        for i in range(3):
            s = self._dc.streams.get_stream_if_exists(SID_FMT.format(i % 3))
            if s:
                s.delete()

        self._dc.streams.bulk_write_datapoints(datapoints)

        for i in range(3):
            stream = self._dc.streams.get_stream(SID_FMT.format(i))
            for j, dp in enumerate(stream.read(newest_first=False)):
                self.assertEqual(dp.get_data(), j * 3 + i)
            stream.delete()

    def test_bulk_write_datapoints_single_stream(self):
        #
        # This test verifies that we can write in bulk a bunch of datapoints to a single
        # stream and read them back.
        #
        datapoints = []
        dt = datetime.datetime.now()
        for i in range(300):
            datapoints.append(DataPoint(
                data_type=STREAM_TYPE_INTEGER,
                units="meters",
                timestamp=dt - datetime.timedelta(seconds=300 - i),
                data=i,
            ))

        stream = self._dc.streams.get_stream_if_exists("pythondc-inttest/test_bulk_write_datapoints_single_stream")
        if stream:
            stream.delete()

        stream = self._dc.streams.get_stream("pythondc-inttest/test_bulk_write_datapoints_single_stream")
        stream.bulk_write_datapoints(datapoints)
        stream_contents_asc = list(stream.read(newest_first=False))
        self.assertEqual(len(stream_contents_asc), 300)
        for i, dp in enumerate(stream_contents_asc):
            self.assertEqual(dp.get_units(), "meters")
            self.assertEqual(dp.get_data_type(), STREAM_TYPE_INTEGER)
            self.assertEqual(dp.get_data(), i)
            self.assertEqual(dp.get_stream_id(), "pythondc-inttest/test_bulk_write_datapoints_single_stream")
            self.assertEqual(dp.get_location(), None)
            self.assertEqual(dp.get_description(), "")
            self.assertIsInstance(dp.get_server_timestamp(), datetime.datetime)
            self.assertIsInstance(dp.get_id(), *six.string_types)
            self.assertEqual(dp.get_quality(), 0)
            self.assertIsInstance(dp.get_timestamp(), datetime.datetime)

        # Cleanup by deleting the stream
        stream.delete()


if __name__ == '__main__':
    dc_inttest_main()
