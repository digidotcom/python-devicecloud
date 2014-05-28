from devicecloud.api.streams import DataStream
from devicecloud.test.test_utilities import HttpTestBase
from devicecloud import DeviceCloudHttpException
import unittest

# Example HTTP Responses

CREATE_DATA_STREAM = {
    "location": "teststream"
}

CREATE_DATA_STREAM_BAD_TYPE = {
    "error": "POST DataStream error. Invalid dataType: foobar"
}

GET_DATA_STREAMS = """
<result>
  <resultSize>2</resultSize>
  <requestedSize>1000</requestedSize>
  <pageCursor>adf3b6ba-3-99f589f4</pageCursor>
  <DataStream>
    <cstId>7383</cstId>
    <streamId>mystream</streamId>
    <dataType>STRING</dataType>
    <forwardTo/>
    <currentValue>
      <id>db1169a0-e5eb-11e3-80d7-fa163ecf1de4</id>
      <timestamp>1401228690667</timestamp>
      <timestampISO>2014-05-27T22:11:30.667Z</timestampISO>
      <serverTimestamp>1401228690667</serverTimestamp>
      <serverTimestampISO>2014-05-27T22:11:30.667Z</serverTimestampISO>
      <data>525</data>
      <description/>
      <quality>0</quality>
    </currentValue>
    <description/>
    <units/>
    <dataTtl>86400</dataTtl>
    <rollupTtl>86400</rollupTtl>
  </DataStream>
  <DataStream>
    <cstId>7383</cstId>
    <streamId>streamname</streamId>
    <dataType>STRING</dataType>
    <forwardTo/>
    <description/>
    <units/>
    <dataTtl>123</dataTtl>
    <rollupTtl>123</rollupTtl>
  </DataStream>
</result>
"""

GET_DATA_STREAMS_EMPTY = """
<result>
  <resultSize>0</resultSize>
  <requestedSize>1000</requestedSize>
  <pageCursor>adf3b6ba-3-99f589f4</pageCursor>
</result>
"""


class TestStreams(HttpTestBase):
    def test_create_data_stream(self):
        self.prepare_json_response("POST", "/ws/DataStream", CREATE_DATA_STREAM)
        stream = self.dc.create_data_stream("teststream",
                                            "string",
                                            description="My Test",
                                            data_ttl=1234,
                                            rollup_ttl=5678)
        self.assertEqual(stream.get_name(), "teststream")
        self.assertEqual(stream.get_data_type(), "string")
        self.assertEqual(stream.get_description(), "My Test")
        self.assertEqual(stream.get_data_ttl(), 1234)
        self.assertEqual(stream.get_rollup_ttl(), 5678)

    def test_create_data_stream_bad_type(self):
        self.prepare_json_response("POST", "/ws/DataStream",
                                   CREATE_DATA_STREAM_BAD_TYPE, status=400)
        self.assertRaises(DeviceCloudHttpException,
                          self.dc.create_data_stream, "teststream", "string")

    def test_get_available_streams_empty(self):
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS_EMPTY)
        self.dc.start()
        streams = self.dc.get_available_streams()
        self.assertEqual(streams, [])

    def test_get_available_streams(self):
        self.prepare_response("GET", "/ws/DataStream", GET_DATA_STREAMS)
        self.dc.start()
        streams = self.dc.get_available_streams()
        self.assertEqual(len(streams), 2)
        self.assertIsInstance(streams[0], DataStream)
        self.assertIsInstance(streams[1], DataStream)


if __name__ == "__main__":
    unittest.main()
