# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
from devicecloud.monitor import MON_TOPIC_ATTR, MON_TRANSPORT_TYPE_ATTR
from devicecloud.test.unit.test_utilities import HttpTestBase
import six

CREATE_TCP_MONITOR_GOOD_REQUEST = """\
<Monitor>
    <monTopic>topA,topB</monTopic>
    <monBatchSize>10</monBatchSize>
    <monFormatType>json</monFormatType>
    <monTransportType>tcp</monTransportType>
    <monCompression>gzip</monCompression>
</Monitor>
"""

CREATE_HTTP_MONITOR_GOOD_REQUEST = """\
<Monitor>
    <monTopic>topA,topB</monTopic>
    <monBatchSize>1</monBatchSize>
    <monFormatType>json</monFormatType>
    <monTransportType>http</monTransportType>
    <monTransportUrl>http://digi.com</monTransportUrl>
    <monTransportToken>None</monTransportToken>
    <monTransportMethod>PUT</monTransportMethod>
    <monConnectTimeout>0</monConnectTimeout>
    <monResponseTimeout>0</monResponseTimeout>
    <monCompression>none</monCompression>
</Monitor>
"""

CREATE_MONITOR_GOOD_RESPONSE = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<result>
  <location>Monitor/178008</location>
</result>
"""

GET_TCP_MONITOR_SINGLE_FOUND = """\
{
    "resultTotalRows": "1",
    "requestedStartRow": "0",
    "resultSize": "1",
    "requestedSize": "1000",
    "remainingSize": "0",
    "items": [
        {
            "monId": "178007",
            "cstId": "7603",
            "monTopic": "DeviceCore,FileDataCore,FileData,DataPoint",
            "monTransportType": "tcp",
            "monFormatType": "json",
            "monBatchSize": "1",
            "monCompression": "zlib",
            "monStatus": "INACTIVE",
            "monBatchDuration": "10"
        }
   ]
}
"""

GET_HTTP_MONITOR_SINGLE_FOUND = """\
{
    "resultTotalRows": "1",
    "requestedStartRow": "0",
    "resultSize": "1",
    "requestedSize": "1000",
    "remainingSize": "0",
    "items": [
        {
            "monId": "178007",
            "cstId": "7603",
            "monTopic": "DeviceCore,FileDataCore,FileData,DataPoint",
            "monTransportType": "http",
            "monFormatType": "json",
            "monBatchSize": "1",
            "monCompression": "none",
            "monStatus": "INACTIVE",
            "monBatchDuration": "0"
        }
   ]
}
"""

GET_TCP_MONITOR_METADTATA = """\
{
    "resultTotalRows": "1",
    "requestedStartRow": "0",
    "resultSize": "1",
    "requestedSize": "1000",
    "remainingSize": "0",
    "items": [
        {
            "monId": "178007",
            "cstId": "7603",
            "monTopic": "DeviceCore,FileDataCore,FileData,DataPoint",
            "monTransportType": "tcp",
            "monFormatType": "json",
            "monBatchSize": "1",
            "monCompression": "zlib",
            "monStatus": "INACTIVE",
            "monBatchDuration": "10"
        }
    ]
}
"""

GET_HTTP_MONITOR_METADTATA = """\
{
    "resultTotalRows": "1",
    "requestedStartRow": "0",
    "resultSize": "1",
    "requestedSize": "1000",
    "remainingSize": "0",
    "items": [
        {
            "monId": "178007",
            "cstId": "7603",
            "monTopic": "DeviceCore,FileDataCore,FileData,DataPoint",
            "monTransportType": "http",
            "monFormatType": "json",
            "monBatchSize": "1",
            "monCompression": "none",
            "monStatus": "INACTIVE",
            "monBatchDuration": "0"
        }
    ]
}
"""

GET_MONITOR_MULTIPLE_FOUND = """\
{
    "resultTotalRows": "2",
    "requestedStartRow": "0",
    "resultSize": "2",
    "requestedSize": "1000",
    "remainingSize": "0",
    "items": [
        {
            "monId": "178007",
            "cstId": "7603",
            "monTopic": "DeviceCore,FileDataCore,FileData,DataPoint",
            "monTransportType": "tcp",
            "monFormatType": "json",
            "monBatchSize": "1",
            "monCompression": "zlib",
            "monStatus": "INACTIVE",
            "monBatchDuration": "10"
        },
        {
            "monId": "178007",
            "cstId": "7603",
            "monTopic": "DeviceCore,FileDataCore,FileData,DataPoint",
            "monTransportType": "tcp",
            "monFormatType": "json",
            "monBatchSize": "1",
            "monCompression": "zlib",
            "monStatus": "INACTIVE",
            "monBatchDuration": "10"
        },
        {
            "monId": "178007",
            "cstId": "7603",
            "monTopic": "DeviceCore,FileDataCore,FileData,DataPoint",
            "monTransportType": "http",
            "monFormatType": "json",
            "monBatchSize": "1",
            "monCompression": "none",
            "monStatus": "INACTIVE",
            "monBatchDuration": "0"
        }
   ]
}
"""

GET_MONITOR_NONE_FOUND = """\
{
    "resultTotalRows": "0",
    "requestedStartRow": "0",
    "resultSize": "0",
    "requestedSize": "1000",
    "remainingSize": "0",
    "items": []
}
"""



class TestMonitorAPI(HttpTestBase):

    def test_create_tcp_monitor(self):
        self.prepare_response("POST", "/ws/Monitor", data=CREATE_MONITOR_GOOD_RESPONSE)
        mon = self.dc.monitor.create_tcp_monitor(['topA', 'topB'], batch_size=10, batch_duration=0,
                                                 compression='gzip', format_type='json')
        self.assertEqual(self._get_last_request().body, six.b(CREATE_TCP_MONITOR_GOOD_REQUEST))
        self.assertEqual(mon.get_id(), 178008)

    def test_create_http_monitor(self):
        self.prepare_response("POST", "/ws/Monitor", data=CREATE_MONITOR_GOOD_RESPONSE)
        mon = self.dc.monitor.create_http_monitor(['topA', 'topB'], 'http://digi.com', transport_token=None,
                                                  transport_method='PUT', connect_timeout=0, response_timeout=0,
                                                  batch_size=1, batch_duration=0, compression='none',
                                                  format_type='json')
        self.assertEqual(self._get_last_request().body, six.b(CREATE_HTTP_MONITOR_GOOD_REQUEST))
        self.assertEqual(mon.get_id(), 178008)

    def test_get_tcp_monitors(self):
        self.prepare_response("GET", "/ws/Monitor", data=GET_TCP_MONITOR_SINGLE_FOUND)
        mons = list(self.dc.monitor.get_monitors((MON_TOPIC_ATTR == "DeviceCore") &
                                                 (MON_TRANSPORT_TYPE_ATTR == "tcp")))
        self.assertEqual(len(mons), 1)
        mon = mons[0]
        self.assertEqual(mon.get_id(), 178007)
        self.assertEqual(self._get_last_request_params(), {
            'condition': "monTopic='DeviceCore' and monTransportType='tcp'",
            'start': '0',
            'size': '1000'
        })

    def test_get_http_monitors(self):
        self.prepare_response("GET", "/ws/Monitor", data=GET_TCP_MONITOR_SINGLE_FOUND)
        mons = list(self.dc.monitor.get_monitors((MON_TOPIC_ATTR == "DeviceCore") &
                                                 (MON_TRANSPORT_TYPE_ATTR == "http")))
        self.assertEqual(len(mons), 1)
        mon = mons[0]
        self.assertEqual(mon.get_id(), 178007)
        self.assertEqual(self._get_last_request_params(), {
            'condition': "monTopic='DeviceCore' and monTransportType='http'",
            'start': '0',
            'size': '1000'
        })

    def test_tcp_get_monitor_present(self):
        self.prepare_response("GET", "/ws/Monitor", data=GET_TCP_MONITOR_SINGLE_FOUND)
        mon = self.dc.monitor.get_monitor(['DeviceCore', 'FileDataCore', 'FileData', 'DataPoint'])
        self.assertEqual(mon.get_id(), 178007)
        self.assertEqual(self._get_last_request_params(), {
            'condition': "monTopic='DeviceCore,FileDataCore,FileData,DataPoint'",
            'start': '0',
            'size': '1000'
        })

    def test_http_get_monitor_present(self):
        self.prepare_response("GET", "/ws/Monitor", data=GET_HTTP_MONITOR_SINGLE_FOUND)
        mon = self.dc.monitor.get_monitor(['DeviceCore', 'FileDataCore', 'FileData', 'DataPoint'])
        self.assertEqual(mon.get_id(), 178007)
        self.assertEqual(self._get_last_request_params(), {
            'condition': "monTopic='DeviceCore,FileDataCore,FileData,DataPoint'",
            'start': '0',
            'size': '1000'
        })

    def test_get_monitor_multiple(self):
        # Should just pick the first result (currently), so results are the same as ever
        self.prepare_response("GET", "/ws/Monitor", data=GET_MONITOR_MULTIPLE_FOUND)
        mon = self.dc.monitor.get_monitor(['DeviceCore', 'FileDataCore', 'FileData', 'DataPoint'])
        self.assertEqual(mon.get_id(), 178007)
        self.assertEqual(self._get_last_request_params(), {
            'condition': "monTopic='DeviceCore,FileDataCore,FileData,DataPoint'",
            'start': '0',
            'size': '1000'
        })

    def test_get_monitor_does_not_exist(self):
        # Should just pick the first result (currently), so results are the same as ever
        self.prepare_response("GET", "/ws/Monitor", data=GET_MONITOR_NONE_FOUND)
        mon = self.dc.monitor.get_monitor(['DeviceCore', 'FileDataCore', 'FileData', 'DataPoint'])
        self.assertEqual(mon, None)


class TestDeviceCloudMonitor(HttpTestBase):

    def setUp(self):
        HttpTestBase.setUp(self)
        self.prepare_response("GET", "/ws/Monitor", data=GET_TCP_MONITOR_SINGLE_FOUND)
        mon = self.dc.monitor.get_monitor(['DeviceCore', 'FileDataCore', 'FileData', 'DataPoint'])
        self.mon = mon

    def test_get_tcp_metadata(self):
        self.prepare_response("GET", "/ws/Monitor/178007", data=GET_TCP_MONITOR_METADTATA)
        self.assertEqual(self.mon.get_metadata(), {
            "monId": "178007",
            "cstId": "7603",
            "monTopic": "DeviceCore,FileDataCore,FileData,DataPoint",
            "monTransportType": "tcp",
            "monFormatType": "json",
            "monBatchSize": "1",
            "monCompression": "zlib",
            "monStatus": "INACTIVE",
            "monBatchDuration": "10"
        })

    def test_delete(self):
        self.prepare_response("DELETE", "/ws/Monitor/178007")
        self.mon.delete()
        req = self._get_last_request()
        self.assertEqual(req.method, "DELETE")
        self.assertEqual(req.path, "/ws/Monitor/178007")

    def test_get_id(self):
        self.assertEqual(self.mon.get_id(), 178007)
