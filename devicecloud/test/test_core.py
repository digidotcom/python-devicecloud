# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.
import json
import unittest
from devicecloud.test.test_utilities import HttpTestBase


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



class TestDeviceCloudConnection(HttpTestBase):

    def test_iter_json_with_params(self):
        it = self.dc._conn.iter_json_pages("/test/path", foo="bar", key="value")
        self.prepare_response("GET", "/test/path", TEST_BASIC_RESPONSE)
        self.assertEqual(len(list(it)), 2)
        self.assertDictEqual(self._get_last_request_params(), {
            "start": "0",
            "foo": "bar",
            "key": "value",
            "size": "1000",
        })

    def test_iter_json_pages_paged_noparams(self):
        it = self.dc._conn.iter_json_pages("/test/path", page_size=1)
        self.prepare_response("GET", "/test/path", TEST_PAGED_RESPONSE_PAGE1)
        self.assertEqual(it.next()["id"], 1)
        self.prepare_response("GET", "/test/path", TEST_PAGED_RESPONSE_PAGE2)
        self.assertEqual(it.next()["id"], 2)
        self.assertDictEqual(self._get_last_request_params(), {
            "size": "1",
            "start": "1"
        })

if __name__ == "__main__":
    unittest.main()
