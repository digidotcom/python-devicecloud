import unittest
from devicecloud import DeviceCloud
from devicecloud.api.sci import DeviceTarget
from devicecloud.test.test_utilities import prepare_json_response, prepare_response
import httpretty

EXAMPLE_SCI_DEVICE_NOT_CONNECTED = """\
<sci_reply version="1.0"><reboot><device id="00000000-00000000-00409DFF-FF58175B"><error id="2001"><desc>Device Not Connected</desc></error></device></reboot></sci_reply>
"""


class TestSCI(unittest.TestCase):

    def setUp(self):
        httpretty.enable()
        self.dc = DeviceCloud('user', 'pass')

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

    def _prepare_sci_response(self, response, status=200):
        prepare_response("POST", "/ws/sci", response, status)

    def test_sci_successful_error(self):
        self._prepare_sci_response(EXAMPLE_SCI_DEVICE_NOT_CONNECTED)
        self.dc._sci.send_sci(
            operation="send_message",
            target=DeviceTarget("00000000-00000000-00409DFF-FF58175B"),
            payload="<reset/>")
        self.assertEqual(httpretty.last_request().body,
                         '<sci_request version="1.0"><send_message><targets><device id="00000000-00000000-00409DFF-FF58175B"/></targets><reset/></send_message></sci_request>')



if __name__ == "__main__":
    unittest.main()
