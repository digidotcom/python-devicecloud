# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

import unittest
import json

from devicecloud import DeviceCloud
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

    def _get_last_request(self):
        return httpretty.last_request()

    def prepare_response(self, method, path, data, status=200, match_querystring=False):
        # TODO:
        #   Should probably assert on more request headers and
        #   respond with correct content type, etc.

        httpretty.register_uri(method,
                               "https://login.etherios.com{}".format(path),
                               data,
                               match_querystring=match_querystring,
                               status=status)

    def prepare_json_response(self, method, path, data, status=200):
        self.prepare_response(method, path, json.dumps(data), status=status)
