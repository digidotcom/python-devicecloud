# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

import unittest

from devicecloud.sci import DeviceTarget
from devicecloud.test.unit.test_utilities import HttpTestBase
import httpretty
import six


EXAMPLE_SCI_DEVICE_NOT_CONNECTED = """\
<sci_reply version="1.0"><reboot><device id="00000000-00000000-00409DFF-FF58175B"><error id="2001"><desc>Device Not Connected</desc></error></device></reboot></sci_reply>
"""


class TestSCI(HttpTestBase):
    def _prepare_sci_response(self, response, status=200):
        self.prepare_response("POST", "/ws/sci", response, status)

    def test_sci_successful_error(self):
        self._prepare_sci_response(EXAMPLE_SCI_DEVICE_NOT_CONNECTED)
        self.dc.get_sci_api().send_sci(
            operation="send_message",
            target=DeviceTarget("00000000-00000000-00409DFF-FF58175B"),
            payload="<reset/>")
        self.assertEqual(httpretty.last_request().body,
                         six.b('<sci_request version="1.0">'
                               '<send_message>'
                               '<targets>'
                               '<device id="00000000-00000000-00409DFF-FF58175B"/>'
                               '</targets>'
                               '<reset/>'
                               '</send_message>'
                               '</sci_request>'))



if __name__ == "__main__":
    unittest.main()
