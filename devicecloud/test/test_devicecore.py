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
from devicecloud.test.test_utilities import HttpTestBase


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


class TestDeviceCore(HttpTestBase):
    def _get_device(self, mac):
        devices = self.dc.devicecore.list_devices()
        self.assertEqual(len(devices), 2)

        # get a ref to device with mac "00:40:9D:58:17:5B"
        for device in devices:
            if device.get_mac() == mac:
                break
        else:
            self.fail("No device with expected MAC address")

        return device

    def test_dc_get_devices(self):
        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        devices = self.dc.devicecore.list_devices()
        self.assertEqual(len(devices), 2)

        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        dev1 = self._get_device("00:40:9D:58:17:5B")

        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        dev2 = self._get_device("00:1d:09:2b:7d:8c")

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

    def test_refresh_from_cache(self):
        get_devices_update = copy.deepcopy(EXAMPLE_GET_DEVICES)
        get_devices_update["items"][0]["dpDeviceType"] = "Turboencabulator"
        del get_devices_update["items"][1]  # remove the other item... close enough
        self.prepare_json_response("GET", "/ws/DeviceCore", EXAMPLE_GET_DEVICES)
        device = self._get_device("00:40:9D:58:17:5B")
        self.prepare_json_response("GET", "/ws/DeviceCore/702077", get_devices_update)
        self.assertEqual(device.get_device_type(), "ConnectPort X5 R")
        self.assertEqual(device.get_device_type(False), "Turboencabulator")
        self.assertEqual(device.get_device_type(), "Turboencabulator")  # make sure cache updated


if __name__ == '__main__':
    unittest.main()
