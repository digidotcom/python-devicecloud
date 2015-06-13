# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
import copy
import datetime
import unittest

from dateutil.tz import tzutc
from devicecloud import DeviceCloudHttpException
from devicecloud.devicecore import dev_mac, group_id
from devicecloud.test.unit.test_utilities import HttpTestBase
import httpretty
from devicecloud.devicecore import ADD_GROUP_TEMPLATE
import six
import mock


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

EXAMPLE_GET_GROUPS = """\
{
  "resultTotalRows": "2",
  "requestedStartRow": "0",
  "resultSize": "2",
  "requestedSize": "1000",
  "remainingSize": "0",
  "items": [
    { "grpId": "11817", "grpName": "7603_Etherios", "grpDescription": "7603_Etherios root group", "grpPath": "\/7603_Etherios\/", "grpParentId": "1"},
    { "grpId": "13542", "grpName": "Demo", "grpPath": "\/7603_Etherios\/Demo\/", "grpParentId": "11817"}
  ]
}
"""

EXAMPLE_GET_GROUPS_EXTENDED = """\
{
  "resultTotalRows": "4",
  "requestedStartRow": "0",
  "resultSize": "4",
  "requestedSize": "1000",
  "remainingSize": "0",
  "items": [
    { "grpId": "11817", "grpName": "7603_Etherios", "grpDescription": "7603_Etherios root group", "grpPath": "\/7603_Etherios\/", "grpParentId": "1"},
    { "grpId": "13542", "grpName": "Demo", "grpPath": "\/7603_Etherios\/Demo\/", "grpParentId": "11817"},
    { "grpId": "13544", "grpName": "SubDir2", "grpPath": "\/7603_Etherios\/Demo\/SubDir2\/", "grpParentId": "13542"},
    { "grpId": "13545", "grpName": "Another Second Level", "grpDescription": "Another Second Level", "grpPath": "\/7603_Etherios\/Another Second Level\/", "grpParentId": "11817"}
  ]
}
"""

PROVISION_SUCCESS_RESPONSE1 = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<result>
  <location>DeviceCore/946246/0</location>
</result>
"""

PROVISION_MULTIPLE_SUCCESS_RESPONSE1 = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<result>
  <location>DeviceCore/1397876/0</location>
  <location>DeviceCore/946246/0</location>
</result>
"""

PROVISION_ERROR1 = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<result>
  <error>The device 00000000-00000000-BC5FF4FF-FFF7908A is already provisioned.</error>
</result>
"""

PROVISION_MIXED_RESULT_RESPONSE = """\
<?xml version="1.0" encoding="ISO-8859-1"?>
<result>
  <location>DeviceCore/1397876/0</location>
  <error>The device 00000000-00000000-D48564FF-FF9D4FEE is already provisioned.</error>
</result>
"""

class TestDeviceCoreGroups(HttpTestBase):

    def test_get_groups(self):
        self.prepare_response("GET", "/ws/Group", EXAMPLE_GET_GROUPS)
        it = self.dc.devicecore.get_groups()

        grp = six.next(it)
        self.assertEqual(grp.is_root(), True)
        self.assertEqual(grp.get_id(), "11817")
        self.assertEqual(grp.get_name(), "7603_Etherios")
        self.assertEqual(grp.get_description(), "7603_Etherios root group")
        self.assertEqual(grp.get_path(), "/7603_Etherios/")
        self.assertEqual(grp.get_parent_id(), "1")

        grp = six.next(it)
        self.assertEqual(grp.is_root(), False)
        self.assertEqual(grp.get_id(), "13542")
        self.assertEqual(grp.get_name(), "Demo")
        self.assertEqual(grp.get_description(), "")
        self.assertEqual(grp.get_path(), "/7603_Etherios/Demo/")
        self.assertEqual(grp.get_parent_id(), "11817")

    def test_repr_and_tree_print(self):
        self.prepare_response("GET", "/ws/Group", EXAMPLE_GET_GROUPS_EXTENDED)
        fobj = six.StringIO()
        root = self.dc.devicecore.get_group_tree_root()
        root.print_subtree(fobj)  # the order of the traversal can vary, so just assert on the length
        if six.PY2:
            self.assertEqual(len(fobj.getvalue()), 513)
        elif six.PY3:
            self.assertEqual(len(fobj.getvalue()), 495)  # no u'' on repr for strings

    def test_get_groups_condition(self):
        self.prepare_response("GET",  "/ws/Group", EXAMPLE_GET_GROUPS)
        list(self.dc.devicecore.get_groups(group_id == "123"))
        params = self._get_last_request_params()
        self.assertEqual(params["condition"], "grpId='123'")


class TestDeviceCoreProvisioning(HttpTestBase):

    def test_provision_one_simple_device_id(self):
        self.prepare_response("POST", "/ws/DeviceCore", PROVISION_SUCCESS_RESPONSE1, status=207)
        res = self.dc.devicecore.provision_device(device_id='00000000-00000000-0000DEFF-FFADBEEFF')
        req = self._get_last_request()
        self.assertEqual(req.body, six.b(
            "<list>"
            "<DeviceCore>"
            "<devConnectwareId>00000000-00000000-0000DEFF-FFADBEEFF</devConnectwareId>"
            "</DeviceCore>"
            "</list>"))
        self.assertDictEqual(res, {"error": False, "error_msg": None, "location": "DeviceCore/946246/0"})

    def test_provision_one_simple_mac(self):
        self.prepare_response("POST", "/ws/DeviceCore", PROVISION_SUCCESS_RESPONSE1, status=207)
        res = self.dc.devicecore.provision_device(mac_address="DE:AD:BE:EF:00:00")
        req = self._get_last_request()
        self.assertEqual(req.body, six.b(
            "<list>"
            "<DeviceCore>"
            "<devMac>DE:AD:BE:EF:00:00</devMac>"
            "</DeviceCore>"
            "</list>"))
        self.assertDictEqual(res, {"error": False, "error_msg": None, "location": "DeviceCore/946246/0"})

    def test_provision_imei(self):
        self.prepare_response("POST", "/ws/DeviceCore", PROVISION_SUCCESS_RESPONSE1, status=207)
        res = self.dc.devicecore.provision_device(imei="990000862471854")
        req = self._get_last_request()
        self.assertEqual(req.body, six.b(
             "<list>"
            "<DeviceCore>"
            "<devCellularModemId>990000862471854</devCellularModemId>"
            "</DeviceCore>"
            "</list>"))
        self.assertDictEqual(res, {"error": False, "error_msg": None, "location": "DeviceCore/946246/0"})

    def test_provision_all_the_fixins(self):
        self.prepare_response("POST", "/ws/DeviceCore", PROVISION_SUCCESS_RESPONSE1, status=207)
        res = self.dc.devicecore.provision_device(
            mac_address="DE:AD:BE:EF:00:00",
            group_path="/group/path",
            metadata="Sweet, sweet metadata",
            map_lat=44.9807496,
            map_long=-93.1397815,
            contact="Saint Paul Parks Department",
            description="Buried Treasure",
        )
        req = self._get_last_request()
        self.assertEqual(req.body, six.b(
            '<list>'
            '<DeviceCore>'
            '<devMac>DE:AD:BE:EF:00:00</devMac>'
            '<grpPath>/group/path</grpPath>'
            '<dpUserMetaData>Sweet, sweet metadata</dpUserMetaData>'
            '<dpMapLong>-93.1397815</dpMapLong>'
            '<dpMapLat>44.9807496</dpMapLat>'
            '<dpContact>Saint Paul Parks Department</dpContact>'
            '<dpDescription>Buried Treasure</dpDescription>'
            '</DeviceCore>'
            '</list>'))
        self.assertDictEqual(res, {"error": False, "error_msg": None, "location": "DeviceCore/946246/0"})

    def test_provision_multiple_simple(self):
        self.prepare_response("POST", "/ws/DeviceCore", PROVISION_MULTIPLE_SUCCESS_RESPONSE1, status=207)
        res = self.dc.devicecore.provision_devices([
            {'device_id': "00000000-00000000-0000DEFF-FFADBEEFF"},
            {'mac_address': 'DE:AD:BE:EF:00:00'}
        ])
        req = self._get_last_request()
        self.assertEqual(req.body, six.b(
                '<list>'
                '<DeviceCore>'
                '<devConnectwareId>00000000-00000000-0000DEFF-FFADBEEFF</devConnectwareId>'
                '</DeviceCore>'
                ''
                '<DeviceCore>'
                '<devMac>DE:AD:BE:EF:00:00</devMac>'
                '</DeviceCore>'
                '</list>'))
        self.assertTrue(len(res), 2)
        self.assertDictEqual(res[0], {"error": False, "error_msg": None, "location": "DeviceCore/1397876/0"})
        self.assertDictEqual(res[1], {"error": False, "error_msg": None, "location": "DeviceCore/946246/0"})

    def test_without_required_param(self):
        self.assertRaises(ValueError, self.dc.devicecore.provision_device, description="I should not work")

    def test_bad_request_400(self):
        self.prepare_response('POST', '/ws/DeviceCore', 'Bad Request', status=400)
        self.assertRaises(DeviceCloudHttpException,
                          self.dc.devicecore.provision_device, mac_address="DE:AD:BE:EF:00:00")

    def test_bad_request_500(self):
        self.prepare_response('POST', '/ws/DeviceCore', 'Bad Request', status=500)
        self.assertRaises(DeviceCloudHttpException,
                          self.dc.devicecore.provision_device, mac_address="DE:AD:BE:EF:00:00")

    def test_error_response(self):
        self.prepare_response("POST", "/ws/DeviceCore", PROVISION_ERROR1, status=207)
        res = self.dc.devicecore.provision_device(imei="990000862471854")
        self.assertDictEqual(res, {
            "error": True,
            "error_msg": 'The device 00000000-00000000-BC5FF4FF-FFF7908A is already provisioned.',
            "location": None}
        )

    def test_mixed_error_success_response(self):
        self.prepare_response("POST", "/ws/DeviceCore", PROVISION_MIXED_RESULT_RESPONSE, status=207)
        res = self.dc.devicecore.provision_devices([
            {'device_id': "00000000-00000000-0000DEFF-FFADBEEFF"},
            {'mac_address': 'DE:AD:BE:EF:00:00'}
        ])
        self.assertTrue(len(res), 2)
        self.assertDictEqual(res[0], {
            'error': False,
            'error_msg': None,
            'location': 'DeviceCore/1397876/0',
        })
        self.assertDictEqual(res[1], {
            'error': True,
            'error_msg': 'The device 00000000-00000000-D48564FF-FF9D4FEE is already provisioned.',
            'location': None,
        })


class TestDeviceCoreDeleting(HttpTestBase):

    def test_delete_device_good(self):
        fake_device = mock.MagicMock()
        fake_device.get_device_id.return_value = '1234'
        self.prepare_response("DELETE", "/ws/DeviceCore/1234", "<result><message>1 items deleted</message></result>", status=200)
        self.dc.devicecore.delete_device(fake_device)
        req = self._get_last_request()
        self.assertEqual(req.path, "/ws/DeviceCore/1234")

    def test_delete_device_not_exist(self):
        fake_device = mock.MagicMock()
        fake_device.get_device_id.return_value = '1234'
        self.prepare_response("DELETE", "/ws/DeviceCore/1234", "<result><message>0 items deleted</message></result>", status=200)
        self.dc.devicecore.delete_device(fake_device)
        req = self._get_last_request()
        self.assertEqual(req.path, "/ws/DeviceCore/1234")

    def test_delete_device_bad_status(self):
        fake_device = mock.MagicMock()
        fake_device.get_device_id.return_value = '1234'
        self.prepare_response("DELETE", "/ws/DeviceCore/1234", "<result><error>I pity da foo' who don' know about API changes.</error></result>", status=400)
        try:
            self.dc.devicecore.delete_device(fake_device)
        except DeviceCloudHttpException:
            pass
        else:
            assert False, "should have thrown exception"
        req = self._get_last_request()
        self.assertEqual(req.path, "/ws/DeviceCore/1234")


class TestDeviceCoreDevices(HttpTestBase):

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
