# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.
import copy
import datetime
import unittest

from dateutil.tz import tzutc
from devicecloud.devicecore import dev_mac
from devicecloud.test.test_utilities import HttpTestBase
import httpretty
from devicecloud.devicecore import ADD_GROUP_TEMPLATE
import six


EXAMPLE_GET_DEVICES = {
    "resultTotalRows": "2",
    "requestedStartRow": "0",
    "resultSize": "2",
    "requestedSize": "1000",
    "remainingSize": "0",
    "items": [
        {
            "id": {
                "devId": "702077",
                "devVersion": "6"
            },
            "devRecordStartDate": "2013-02-28T19:54:00.000Z",
            "devMac": "00:40:9D:58:17:5B",
            "devCellularModemId": "354374042391400",
            "devConnectwareId": "00000000-00000000-00409DFF-FF58175B",
            "cstId": "1872",
            "grpId": "2331",
            "devEffectiveStartDate": "2013-02-28T19:53:00.000Z",
            "devTerminated": "false",
            "dvVendorId": "4261412864",
            "dpDeviceType": "ConnectPort X5 R",
            "dpFirmwareLevel": "34537482",
            "dpFirmwareLevelDesc": "2.15.0.10",
            "dpRestrictedStatus": "0",
            "dpLastKnownIp": "10.35.1.107",
            "dpGlobalIp": "204.182.3.237",
            "dpConnectionStatus": "0",
            "dpLastConnectTime": "2013-04-08T04:01:20.633Z",
            "dpContact": "",
            "dpDescription": "",
            "dpLocation": "",
            "dpMapLat": "34.964465",
            "dpMapLong": "40.268198",
            "dpServerId": "",
            "dpZigbeeCapabilities": "0",
            "dpCapabilities": "6707",
            "grpPath": "",
            "dpLastDisconnectTime": "2013-04-16T19:46:06.557Z"
        },
        {
            "id": {
                "devId": "714038",
                "devVersion": "7"
            },
            "devRecordStartDate": "2013-07-16T18:05:00.000Z",
            "devMac": "00:1d:09:2b:7d:8c",
            "devConnectwareId": "00000000-00000000-001D09FF-FF2B7D8C",
            "cstId": "1872",
            "grpId": "2331",
            "devEffectiveStartDate": "2013-07-16T18:05:00.000Z",
            "devTerminated": "false",
            "dvVendorId": "50331982",
            "dpDeviceType": "IntelligentSystem",
            "dpFirmwareLevel": "0",
            "dpRestrictedStatus": "0",
            "dpLastKnownIp": "10.35.1.113",
            "dpGlobalIp": "204.182.3.238",
            "dpConnectionStatus": "0",
            "dpLastConnectTime": "2013-07-24T00:40:20.363Z",
            "dpServerId": "",
            "dpCapabilities": "66114",
            "grpPath": "",
            "dpLastDisconnectTime": "2013-07-24T00:40:36.537Z"
        }
    ]
}


GET_DEVICES_PAGE1 = """\
{
    "resultTotalRows": "2",
    "requestedStartRow": "0",
    "resultSize": "1",
    "requestedSize": "1",
    "remainingSize": "1",
    "items": [
 {"id": {"devId": "702077","devVersion": "6"},"devRecordStartDate": "2013-02-28T19:54:00.000Z","devMac": "00:40:9D:58:17:5B","devCellularModemId": "354374042391400","devConnectwareId": "00000000-00000000-00409DFF-FF58175B","cstId": "1872","grpId": "2331","devEffectiveStartDate": "2013-02-28T19:53:00.000Z","devTerminated": "false","dvVendorId": "4261412864","dpDeviceType": "ConnectPort X5 R","dpFirmwareLevel": "34537482","dpFirmwareLevelDesc": "2.15.0.10","dpRestrictedStatus": "0","dpLastKnownIp": "10.35.1.107","dpGlobalIp": "204.182.3.237","dpConnectionStatus": "0","dpLastConnectTime": "2013-04-08T04:01:20.633Z","dpContact": "","dpDescription": "","dpLocation": "","dpMapLat": "34.964465","dpMapLong": "40.268198","dpServerId": "","dpZigbeeCapabilities": "0","dpCapabilities": "6707","grpPath": "","dpLastDisconnectTime": "2013-04-16T19:46:06.557Z"}
   ]
 }
"""

GET_DEVICES_PAGE2 = """\
{
    "resultTotalRows": "2",
    "requestedStartRow": "1",
    "resultSize": "1",
    "requestedSize": "1",
    "remainingSize": "0",
    "items": [
 {"id": {"devId": "702078","devVersion": "6"},"devRecordStartDate": "2013-02-28T19:54:00.000Z","devMac": "00:40:9D:58:17:5B","devCellularModemId": "354374042391400","devConnectwareId": "00000000-00000000-00409DFF-FF58175B","cstId": "1872","grpId": "2331","devEffectiveStartDate": "2013-02-28T19:53:00.000Z","devTerminated": "false","dvVendorId": "4261412864","dpDeviceType": "ConnectPort X5 R","dpFirmwareLevel": "34537482","dpFirmwareLevelDesc": "2.15.0.10","dpRestrictedStatus": "0","dpLastKnownIp": "10.35.1.107","dpGlobalIp": "204.182.3.237","dpConnectionStatus": "0","dpLastConnectTime": "2013-04-08T04:01:20.633Z","dpContact": "","dpDescription": "","dpLocation": "","dpMapLat": "34.964465","dpMapLong": "40.268198","dpServerId": "","dpZigbeeCapabilities": "0","dpCapabilities": "6707","grpPath": "","dpLastDisconnectTime": "2013-04-16T19:46:06.557Z"}
   ]
 }
"""


class TestDeviceCore(HttpTestBase):
    def test_dc_get_devices(self):
        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        devices = self.dc.devicecore.get_devices()
        dev1 = six.next(devices)
        dev2 = six.next(devices)
        self.assertRaises(StopIteration, six.next, devices)

        self.assertEqual(dev1.get_mac(), "00:40:9D:58:17:5B")
        self.assertEqual(dev1.get_mac_last4(), "175B")
        self.assertEqual(dev1.get_device_id(), "702077")
        self.assertEqual(dev1.get_connectware_id(), "00000000-00000000-00409DFF-FF58175B")
        self.assertEqual(dev1.get_ip(), "10.35.1.107")
        self.assertEqual(dev1.get_tags(), [])
        self.assertEqual(dev1.get_registration_dt(),
                         datetime.datetime(2013, 2, 28, 19, 54, tzinfo=tzutc()))
        self.assertEqual(dev1.get_meid(), '354374042391400')
        self.assertEqual(dev1.get_customer_id(), '1872')
        self.assertEqual(dev1.get_group_id(), '2331')
        self.assertEqual(dev1.get_group_path(), '')
        self.assertEqual(dev1.get_vendor_id(), '4261412864')
        self.assertEqual(dev1.get_device_type(), 'ConnectPort X5 R')
        self.assertEqual(dev1.get_firmware_level(), '34537482')
        self.assertEqual(dev1.get_firmware_level_description(), '2.15.0.10')
        self.assertEqual(dev1.get_restricted_status(), "0")
        self.assertEqual(dev1.get_last_known_ip(), '10.35.1.107')
        self.assertEqual(dev1.get_global_ip(), '204.182.3.237')
        self.assertEqual(dev1.get_last_connected_dt(),
                         datetime.datetime(2013, 4, 8, 4, 1, 20, 633, tzinfo=tzutc()))
        self.assertEqual(dev1.get_contact(), '')
        self.assertEqual(dev1.get_description(), '')
        self.assertEqual(dev1.get_location(), '')
        self.assertEqual(dev1.get_latlon(), (34.964465, 40.268198))
        self.assertEqual(dev1.get_user_metadata(), None)
        self.assertEqual(dev1.get_zb_pan_id(), None)
        self.assertEqual(dev1.get_zb_extended_address(), None)
        self.assertEqual(dev1.get_server_id(), '')
        self.assertEqual(dev1.get_provision_id(), None)
        self.assertEqual(dev1.get_current_connect_pw(), None)

    def test_dc_get_devices_paged(self):
        self.prepare_response("GET", "/ws/DeviceCore", GET_DEVICES_PAGE1)
        gen = self.dc.devicecore.get_devices(page_size=1)
        dev1 = six.next(gen)
        self.prepare_response("GET", "/ws/DeviceCore", GET_DEVICES_PAGE2)
        dev2 = six.next(gen)
        self.assertRaises(StopIteration, six.next, gen)
        self.assertEqual(dev1.get_device_id(), '702077')
        self.assertEqual(dev2.get_device_id(), '702078')

    def test_dc_get_devices_with_condition(self):
        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        gen = self.dc.devicecore.get_devices(dev_mac == 'xx:xx:xx:xx:xx', page_size=1)
        six.next(gen)
        qs = httpretty.last_request().querystring
        self.assertEqual(qs['condition'][0], "devMac='xx:xx:xx:xx:xx'")
        self.assertEqual(qs['size'][0], "1")
        self.assertEqual(qs['embed'][0], "true")
        self.assertEqual(qs['start'][0], "0")

    def test_refresh_from_cache(self):
        get_devices_update = copy.deepcopy(EXAMPLE_GET_DEVICES)
        get_devices_update["items"][0]["dpDeviceType"] = "Turboencabulator"
        del get_devices_update["items"][1]  # remove the other item... close enough
        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        devices = self.dc.devicecore.get_devices()
        device = six.next(devices)
        self.prepare_json_response("GET", "/ws/DeviceCore/702077", get_devices_update)
        self.assertEqual(device.get_device_type(), "ConnectPort X5 R")
        self.assertEqual(device.get_device_type(False), "Turboencabulator")
        self.assertEqual(device.get_device_type(), "Turboencabulator")  # make sure cache updated

    def test_add_device_to_group(self):
        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        self.prepare_response("PUT", "/ws/DeviceCore", '')
        gen = self.dc.devicecore.get_devices(page_size=1)
        dev = six.next(gen)
        expected = ADD_GROUP_TEMPLATE.format(connectware_id=dev.get_connectware_id(),
                                             group_path='testgrp')
        dev.add_to_group('testgrp')
        self.assertIsNone(dev._device_json)
        self.assertEqual(six.b(expected), httpretty.last_request().body)

    def test_remove_device_from_group(self):
        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        self.prepare_response("PUT", "/ws/DeviceCore", '')
        gen = self.dc.devicecore.get_devices(page_size=1)
        dev = six.next(gen)
        dev.get_group_path = lambda: 'something other than empty string'
        expected = ADD_GROUP_TEMPLATE.format(connectware_id=dev.get_connectware_id(),
                                             group_path='')
        dev.remove_from_group()
        self.assertIsNone(dev._device_json)
        self.assertEqual(six.b(expected), httpretty.last_request().body)

if __name__ == '__main__':
    unittest.main()
