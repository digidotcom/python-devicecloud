# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
import unittest

from devicecloud import DeviceCloudHttpException
from devicecloud.test.unit.test_utilities import HttpTestBase
from mock import patch, call
import six


TEST_BASIC_RESPONSE = """\
{
    "resultTotalRows": "2",
    "requestedStartRow": "0",
    "resultSize": "2",
    "requestedSize": "1000",
    "remainingSize": "0",
    "items": [
        { "id": 1, "name": "bob" },
        { "id": 2, "name": "tim" }
    ]
}
"""

TEST_PAGED_RESPONSE_PAGE1 = """\
{
    "resultTotalRows": "2",
    "requestedStartRow": "0",
    "resultSize": "1",
    "requestedSize": "1",
    "remainingSize": "1",
    "items": [
        { "id": 1, "name": "bob" }
    ]
}
"""

TEST_PAGED_RESPONSE_PAGE2 = """\
{
    "resultTotalRows": "2",
    "requestedStartRow": "1",
    "resultSize": "1",
    "requestedSize": "1",
    "remainingSize": "0",
    "items": [
        { "id": 2, "name": "tim" }
    ]
}
"""

TEST_ERROR_RESPONSE = six.b("""\
<sci_reply version="1.0"><send_message><device id="00000000-00000000-00409DFF-FF736460"><error id="303">\
<desc>Invalid target. Device not found.</desc></error></device>\
<error>Invalid SCI request. No valid targets found.</error></send_message></sci_reply>\
""")


class TestDeviceCloudConnection(HttpTestBase):

    @patch("time.sleep", return_value=None)
    def test_throttle_retries(self, patched_time_sleep):
        self.prepare_response("GET", "/test/path", "", status=429)
        self.assertRaises(DeviceCloudHttpException, self.dc.get_connection().get, "/test/path", retries=5)
        patched_time_sleep.assert_has_calls([
            call(1.5 ** 0),
            call(1.5 ** 1),
            call(1.5 ** 2),
            call(1.5 ** 3),
            call(1.5 ** 4),
        ])

    def test_iter_json_with_params(self):
        it = self.dc.get_connection().iter_json_pages("/test/path", foo="bar", key="value")
        self.prepare_response("GET", "/test/path", TEST_BASIC_RESPONSE)
        self.assertEqual(len(list(it)), 2)
        self.assertDictEqual(self._get_last_request_params(), {
            "start": "0",
            "foo": "bar",
            "key": "value",
            "size": "1000",
        })

    def test_iter_json_pages_paged_noparams(self):
        it = self.dc.get_connection().iter_json_pages("/test/path", page_size=1)
        self.prepare_response("GET", "/test/path", TEST_PAGED_RESPONSE_PAGE1)
        self.assertEqual(six.next(it)["id"], 1)
        self.prepare_response("GET", "/test/path", TEST_PAGED_RESPONSE_PAGE2)
        self.assertEqual(six.next(it)["id"], 2)
        self.assertDictEqual(self._get_last_request_params(), {
            "size": "1",
            "start": "1"
        })

    def test_http_exception(self):
        self.prepare_response("POST", "/test/path", TEST_ERROR_RESPONSE, status=400)
        try:
            self.dc.get_connection().post("/test/path", "bad data")
        except DeviceCloudHttpException as e:
            str(e)  # ensure this does not stack trace at least
            self.assertEqual(e.response.status_code, 400)
            self.assertEqual(e.response.content, TEST_ERROR_RESPONSE)
        else:
            self.fail("DeviceCloudHttpException not raised")

if __name__ == "__main__":
    unittest.main()
