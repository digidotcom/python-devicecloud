import json
from devicecloud import DeviceCloudByEtherios
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



def _cloud_uri(path):
    return "http://login.etherios.com{}".format(path)


class TestDeviceCore(unittest.TestCase):

    def setUp(self):
        httpretty.enable()
        self.dc = DeviceCloudByEtherios('user', 'pass')

    def _prepare_json_response(self, path, data):
        # TODO: should probably assert on more request headers and respond with
        # correct content type, etc.
        httpretty.register_uri(
            httpretty.GET,
            _cloud_uri(path),
            json.dumps(data))

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

    def test_dc_get_devices(self):
        self._prepare_json_response("/ws/DeviceCore/.json", EXAMPLE_GET_DEVICES)
        devices = self.dc.dc_get_devices()
        self.assertEqual(len(devices), 2)

        # get a ref to device with mac "00:40:9D:58:17:5B"
        for device in devices:
            if device.mac == "00:40:9D:58:17:5B":
                break
        else:
            self.fail("No device with expected MAC address")

        self.assertEqual(device.mac, "00:40:9D:58:17:5B")
        self.assertEqual(device.device_id, "702077")
        self.assertEqual(device.ip, "10.35.1.107")
        self.assertEqual(device.tags, [])



if __name__ == '__main__':
    unittest.main()
