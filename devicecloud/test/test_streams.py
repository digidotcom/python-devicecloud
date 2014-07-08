# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

import unittest
import datetime

from devicecloud.streams import DataStream, STREAM_TYPE_FLOAT, DataPoint
from devicecloud.test.test_utilities import HttpTestBase
from devicecloud import DeviceCloudHttpException


# Example HTTP Responses
import httpretty
import six

CREATE_DATA_STREAM = {
    "location": "teststream"
}

CREATE_DATA_STREAM_BAD_TYPE = {
    "error": "POST DataStream error. Invalid dataType: foobar"
}

CREATE_DATAPOINT_RESPONSE = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<result>
  <location>DataPoint/test/07d77854-0557-11e4-ab44-fa163e7ebc6b</location>
</result>
"""

GET_DATA_STREAMS = """
{
    "resultSize": "2",
    "requestedSize": "1000",
    "pageCursor": "9d870afb-2-af668f74",
    "items": [
        {
            "cstId": "7603",
            "streamId": "another\/test",
            "dataType": "INTEGER",
            "forwardTo": "",
            "description": "Some Integral Thing",
            "units": "",
            "dataTtl": "172800",
            "rollupTtl": "432000"
        },
        {
            "cstId": "7603",
            "streamId": "test",
            "dataType": "FLOAT",
            "forwardTo": "",
            "description": "some description",
            "units": "light years",
            "dataTtl": "172800",
            "rollupTtl": "432000"
        }
    ]
}
"""

GET_DATA_STREAMS_EMPTY = """
{
    "resultSize": "0",
    "requestedSize": "1000",
    "pageCursor": "baefe8fa-0-58fd947b",
    "items": []
}
"""

GET_TEST_DATA_STREAM = """\
{
"resultSize": "1",
"requestedSize": "1000",
"pageCursor": "88afa98e-1-7efbf125",
"items": [
{
    "cstId": "7603",
    "streamId": "test",
    "dataType": "FLOAT",
    "forwardTo": "",
    "currentValue": {
        "id": "07d77854-0557-11e4-ab44-fa163e7ebc6b",
        "timestamp": "1404683207981",
        "timestampISO": "2014-07-06T21:46:47.981Z",
        "serverTimestamp": "1404683207981",
        "serverTimestampISO": "2014-07-06T21:46:47.981Z",
        "data": "123.1",
        "description": "Test",
        "quality": "20",
        "location": "1.0,2.0,3.0"
    },
    "description": "some description",
    "units": "light years",
    "dataTtl": "172800",
    "rollupTtl": "432000"}
]
}
"""

GET_TEST_DATA_STREAM_NO_CURRENT_VALUE = """\
{
"resultSize": "1",
"requestedSize": "1000",
"pageCursor": "88afa98e-1-7efbf125",
"items": [
{ "cstId": "7603", "streamId": "test", "dataType": "FLOAT", "forwardTo": "", "description": "some description", "units": "light years", "dataTtl": "172800", "rollupTtl": "432000"}
]
}
"""


GET_STREAM_RESULT = {
    u'items': [
        {u'cstId': u'7603',
         u'dataTtl': u'1234',
         u'dataType': u'STRING',
         u'description': u'My Test',
         u'forwardTo': u'',
         u'rollupTtl': u'5678',
         u'streamId': u'teststream',
         u'units': u''}
    ],
    u'pageCursor': u'b8773c45-1-5a7afea7',
    u'requestedSize': u'1000',
    u'resultSize': u'1'
}


class TestStreamsAPI(HttpTestBase):

    def test_create_data_stream(self):
        self.prepare_json_response("POST", "/ws/DataStream", CREATE_DATA_STREAM)
        self.prepare_json_response("GET", "/ws/DataStream/teststream", GET_STREAM_RESULT)
        streams = self.dc.get_streams_api()
        stream = streams.create_stream("teststream",
                                            "string",
                                            description="My Test",
                                            data_ttl=1234,
                                            rollup_ttl=5678)
        self.assertEqual(stream.get_stream_id(), "teststream")
        self.assertEqual(stream.get_data_type(), "STRING")
        self.assertEqual(stream.get_description(), "My Test")
        self.assertEqual(stream.get_data_ttl(), 1234)
        self.assertEqual(stream.get_rollup_ttl(), 5678)

    def test_create_data_stream_bad_type(self):
        self.prepare_json_response("POST", "/ws/DataStream",
                                   CREATE_DATA_STREAM_BAD_TYPE, status=400)
        self.assertRaises(DeviceCloudHttpException,
                          self.dc.streams.create_stream, "teststream", "string")

    def test_get_streams_empty(self):
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS_EMPTY)
        streams = self.dc.streams.get_streams()
        self.assertEqual(list(streams), [])

    def test_get_streams(self):
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS)
        streams = list(self.dc.streams.get_streams())
        self.assertEqual(len(streams), 2)
        self.assertIsInstance(streams[0], DataStream)
        self.assertIsInstance(streams[1], DataStream)

    def test_get_stream(self):
        # Get a stream by ID when there is no cache
        stream = self.dc.streams.get_stream("/test/stream")
        self.assert_(isinstance(stream, DataStream))
        self.assertEqual(stream.get_stream_id(), "/test/stream")

    def test_get_stream_if_exists_does_not_exist(self):
        # Try to get a stream that does not exist
        self.prepare_response("GET", "/ws/DataStream/test", "", status=404)
        self.assertEqual(self.dc.streams.get_stream_if_exists("test"), None)

    def test_get_stream_if_exists_exists(self):
        # Try to get a stream that does exist
        self.prepare_response("GET", "/ws/DataStream/test", GET_TEST_DATA_STREAM, status=200)
        stream = self.dc.streams.get_stream_if_exists("test")
        self.assert_(stream is not None)
        self.assertEqual(stream.get_stream_id(), "test")
        self.assertEqual(stream.get_rollup_ttl(), 432000)


class TestDataStream(HttpTestBase):

    def _get_stream(self, response):
        self.prepare_response("GET", "/ws/DataStream/test", response)
        return self.dc.streams.get_stream("test")

    def test_bad_cached_data(self):
        # mostly for branch coverage
        self.assertRaises(TypeError, DataStream, self.dc._conn, "test", 3)

    def test_repr(self):
        self.assertEqual(repr(self._get_stream(GET_TEST_DATA_STREAM)), "DataStream('test')")

    def test_accessors(self):
        stream = self._get_stream(GET_TEST_DATA_STREAM)

        # all of these should be cached
        self.assertEqual(stream.get_stream_id(), "test")
        self.assertEqual(stream.get_data_ttl(), 172800)
        self.assertEqual(stream.get_rollup_ttl(), 432000)
        self.assertEqual(stream.get_description(), "some description")
        self.assertEqual(stream.get_units(), "light years")
        self.assertEqual(stream.get_data_type(), STREAM_TYPE_FLOAT)

        # for this one, we are required to make an HTTP request to get the
        # latest value
        self.assertEqual(stream.get_current_value().get_data(), 123.1)

    def test_get_current_value_empty(self):
        stream = self._get_stream(GET_TEST_DATA_STREAM_NO_CURRENT_VALUE)
        self.assertEqual(stream.get_current_value(), None)

    def test_write_bad_arg(self):
        test_stream = self._get_stream(GET_TEST_DATA_STREAM)
        self.assertRaises(TypeError, test_stream.write, 123)

    def test_write_simple(self):
        self.prepare_response("POST", "/ws/DataPoint/test", CREATE_DATAPOINT_RESPONSE, status=201)
        test_stream = self._get_stream(GET_TEST_DATA_STREAM)
        test_stream.write(DataPoint(
            data=123.4,
        ))

        # verify that the body sent to the device cloud is sufficiently minimal
        self.assertEqual(
            httpretty.last_request().body,
            six.b('<DataPoint>'
                  '<streamId>test</streamId>'
                  '<data>123.4</data>'
                  '</DataPoint>'))

    def test_write_full(self):
        self.prepare_response("POST", "/ws/DataPoint/test", CREATE_DATAPOINT_RESPONSE, status=201)
        test_stream = self._get_stream(GET_TEST_DATA_STREAM)
        test_stream.write(DataPoint(
            data=123.4,
            description="Best Datapoint Ever?",
            timestamp=datetime.datetime(2014, 7, 7, 14, 10, 34),
            quality=99,
            location=(99, 88, 77),
            units="scolvilles",
        ))

        # verify that the body sent to the device cloud is sufficiently minimal
        self.assertEqual(
            httpretty.last_request().body,
            six.b('<DataPoint>'
                  '<streamId>test</streamId>'
                  '<data>123.4</data>'
                  '<description>Best Datapoint Ever?</description>'
                  '<timestamp>2014-07-07T14:10:34</timestamp>'  # TODO: does this need to include tz?
                  '<quality>99</quality>'
                  '<location>99,88,77</location>'
                  '<streamUnits>scolvilles</streamUnits>'
                  '</DataPoint>'))


class TestDataPoint(HttpTestBase):

    def _get_stream(self, stream_id="test", with_cached_data=False):
        if with_cached_data:
            self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS)
            self.dc.streams.get_streams()
            return self.dc.streams.get_stream(stream_id)
        else:
            return self.dc.streams.get_stream(stream_id)

    def test_accessors(self):
        # With a captured data point, ensure we can read back everything as expected
        stream = self._get_stream("test", with_cached_data=True)
        self.prepare_response("GET", "/ws/DataStream/test", GET_TEST_DATA_STREAM)

        dp = stream.get_current_value()
        self.assertEqual(dp.get_id(), "07d77854-0557-11e4-ab44-fa163e7ebc6b")
        self.assertEqual(dp.get_timestamp(), datetime.datetime(2014, 7, 6, 21, 46, 47, 981000))
        self.assertEqual(dp.get_server_timestamp(), datetime.datetime(2014, 7, 6, 21, 46, 47, 981000))
        self.assertEqual(dp.get_data(), 123.1)
        self.assertEqual(dp.get_description(), "Test")
        self.assertEqual(dp.get_quality(), 20)
        self.assertEqual(dp.get_location(), (1.0, 2.0, 3.0))
        self.assertEqual(dp.get_units(), "light years")
        self.assertEqual(dp.get_stream_id(), "test")
        self.assertEqual(dp.get_data_type(), "FLOAT")

    def test_bad_location_string(self):
        dp = DataPoint(123)
        self.assertRaises(ValueError, dp.set_location, "0,1")
        self.assertRaises(ValueError, dp.set_location, "0,1,2,3")
        self.assertRaises(ValueError, dp.set_location, "bad-input")

    def test_bad_location_type(self):
        dp = DataPoint(123)
        self.assertRaises(TypeError, dp.set_location, datetime.datetime.now())

    def test_set_location_valid(self):
        dp = DataPoint(123)
        dp.set_location((4, 5, 6))
        self.assertEqual(dp.get_location(), (4.0, 5.0, 6.0))

    def test_set_quality_float(self):
        # cover truncation case for code coverage
        dp = DataPoint(123)
        dp.set_quality(99.5)
        self.assertEqual(dp.get_quality(), 99)

    def test_type_checking(self):
        dp = DataPoint(123)
        self.assertRaises(TypeError, dp.set_description, 5)
        self.assertRaises(TypeError, dp.set_stream_id, [1, 2, 3])

    def test_set_bad_timestamp(self):
        dp = DataPoint(123)
        self.assertRaises(ValueError, dp.set_timestamp, "123456")  # not ISO8601
        self.assertRaises(TypeError, dp.set_timestamp, 12345)

if __name__ == "__main__":
    unittest.main()
