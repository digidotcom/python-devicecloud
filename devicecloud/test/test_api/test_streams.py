# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

import unittest

from devicecloud.streams import DataStream
from devicecloud.test.test_utilities import HttpTestBase
from devicecloud import DeviceCloudHttpException


# Example HTTP Responses

CREATE_DATA_STREAM = {
    "location": "teststream"
}

CREATE_DATA_STREAM_BAD_TYPE = {
    "error": "POST DataStream error. Invalid dataType: foobar"
}

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
            "units": "",
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
"pageCursor": "3bff891c-1-ffa063ca",
"items": [
{ "cstId": "7603", "streamId": "test", "dataType": "FLOAT", "forwardTo": "", "description": "some description", "units": "", "dataTtl": "172800", "rollupTtl": "432000"}
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

class TestStreams(HttpTestBase):

    def test_create_data_stream(self):
        self.prepare_json_response("POST", "/ws/DataStream", CREATE_DATA_STREAM)
        self.prepare_json_response("GET", "/ws/DataStream/teststream", GET_STREAM_RESULT)
        streams = self.dc.get_streams_api()
        stream = streams.create_data_stream("teststream",
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
        streams = self.dc.get_streams_api()
        self.assertRaises(DeviceCloudHttpException,
                          streams.create_data_stream, "teststream", "string")

    def test_get_streams_empty(self):
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS_EMPTY)
        streamsapi = self.dc.get_streams_api()
        streams = streamsapi.get_streams()
        self.assertEqual(streams, [])

    def test_get_streams(self):
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS)
        streamsapi = self.dc.get_streams_api()
        streams = streamsapi.get_streams()
        self.assertEqual(len(streams), 2)
        self.assertIsInstance(streams[0], DataStream)
        self.assertIsInstance(streams[1], DataStream)

    def test_get_stream_no_cache(self):
        # Get a stream by ID when there is no cache
        stream = self.dc.get_streams_api().get_stream("/test/stream")
        self.assert_(isinstance(stream, DataStream))
        self.assertEqual(stream.get_stream_id(), "/test/stream")

    def test_get_stream_cache_miss(self):
        # Fill (empty) cache
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS_EMPTY)
        streamsapi = self.dc.get_streams_api()
        streams = streamsapi.get_streams()
        self.assertEqual(streams, [])

        # Now get a stream by ID
        stream = streamsapi.get_stream("/test/stream")
        self.assert_(isinstance(stream, DataStream))
        self.assertEqual(stream.get_stream_id(), "/test/stream")

    def test_get_stream_cache_hit(self):
        # Fill cache by doing a get_steams() call
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS)
        streamsapi = self.dc.get_streams_api()
        streams = streamsapi.get_streams()
        self.assertEqual(len(streams), 2)
        self.assertIsInstance(streams[0], DataStream)
        self.assertIsInstance(streams[1], DataStream)

        # Now, let's do a get_stream for stream 0
        test_stream = streamsapi.get_stream("test")
        self.assertEqual(test_stream.get_stream_id(), "test")
        self.assertEqual(test_stream.get_data_ttl(), 172800)  # no HTTP request to retrieve

    def test_get_stream_if_exists_nocache_does_not_exist(self):
        # In this test, we try to get a stream that does not exist from a state in
        # which no cache exists.  The stream does not exist, so we give a 404
        self.prepare_response("GET", "/ws/DataStream/test", "", status=404)
        streamsapi = self.dc.get_streams_api()
        self.assertEqual(streamsapi.get_stream_if_exists("test"), None)

    def test_get_stream_if_exists_cache_miss_does_not_exist(self):
        # In this test, we try to get a stream that does not exist from a state in
        # which a cache does exist.  In this case, we still expect a request against
        # the device cloud to be made, but we will return a 404
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS_EMPTY)
        self.prepare_response("GET", "/ws/DataStream/test", "", status=404)
        streamsapi = self.dc.get_streams_api()
        streamsapi.get_streams()
        self.assertEqual(streamsapi.get_stream_if_exists("test"), None)

    def test_get_stream_if_exists_cache_hit(self):
        # In this case, we request to get a stream if it exists.  We have a
        # cache containing the stream, so we just provide that stream
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS)
        streamsapi = self.dc.get_streams_api()
        streams = streamsapi.get_streams()
        stream = streamsapi.get_stream_if_exists("test")
        self.assert_(stream is not None)
        self.assertEqual(stream.get_stream_id(), "test")
        self.assertEqual(stream.get_rollup_ttl(), 432000)

    def test_get_stream_if_exists_nocache_exists(self):
        # In this case, there is no cache but we have requested a stream that
        # does in fact exist
        self.prepare_response("GET", "/ws/DataStream/test", GET_TEST_DATA_STREAM)
        streamsapi = self.dc.get_streams_api()
        stream = streamsapi.get_stream_if_exists("test")
        self.assert_(stream is not None)
        self.assertEqual(stream.get_stream_id(), "test")
        self.assertEqual(stream.get_data_type(), "FLOAT")
        self.assertEqual(stream.get_description(), "some description")
        self.assertEqual(stream.get_current_value(), 0)

if __name__ == "__main__":
    unittest.main()
