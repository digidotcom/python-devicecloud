from devicecloud import DeviceCloud
from devicecloud.test.test_utilities import prepare_json_response
import httpretty
import unittest


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



class TestDeviceCore(unittest.TestCase):

    def setUp(self):
        httpretty.enable()
        self.dc = DeviceCloud('user', 'pass')

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

    def test_dc_get_devices(self):
        prepare_json_response("GET", "/ws/DeviceCore/.json", EXAMPLE_GET_DEVICES)
        devices = self.dc.list_devices()
        self.assertEqual(len(devices), 2)

        # get a ref to device with mac "00:40:9D:58:17:5B"
        for device in devices:
            if device.get_mac() == "00:40:9D:58:17:5B":
                break
        else:
            self.fail("No device with expected MAC address")

        self.assertEqual(device.get_mac(), "00:40:9D:58:17:5B")
        self.assertEqual(device.get_mac_last4(), "175B")
        self.assertEqual(device.get_device_id(), "702077")
        self.assertEqual(device.get_connectware_id(), "00000000-00000000-00409DFF-FF58175B")
        self.assertEqual(device.get_ip(), "10.35.1.107")
        self.assertEqual(device.get_tags(), [])


if __name__ == '__main__':
    unittest.main()
