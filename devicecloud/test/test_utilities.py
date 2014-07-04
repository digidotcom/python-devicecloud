from devicecloud import DeviceCloud
import unittest
import json
import httpretty


class HttpTestBase(unittest.TestCase):
    def setUp(self):
        httpretty.enable()
        # setup the Device cloud ping response
        self.prepare_response("GET", "/ws/DeviceCore?size=1", "", status=200)
        self.dc = DeviceCloud('user', 'pass')

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

    def prepare_response(self, method, path, data, status=200):
        # TODO:
        #   Should probably assert on more request headers and
        #   respond with correct content type, etc.

        httpretty.register_uri(method,
                               "https://login.etherios.com{}".format(path),
                               data,
                               status=status)

    def prepare_json_response(self, method, path, data, status=200):
        self.prepare_response(method, path, json.dumps(data), status=status)
