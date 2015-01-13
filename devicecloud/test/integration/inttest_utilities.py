# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from getpass import getpass
import unittest

from devicecloud import DeviceCloud
import os
from six.moves import input


class DeviceCloudIntegrationTestCase(unittest.TestCase):

    def setUp(self):
        if not os.environ.get("RUN_INTEGRATION_TESTS", False):
            self.skipTest("Not performing integration tests")
        else:
            self._username = os.environ.get("DC_USERNAME", None)
            self._password = os.environ.get("DC_PASSWORD", None)
            self._base_url = os.environ.get("DC_URL", None)  # will use default if unspecified
            if not self._username or not self._password:
                self.fail("DC_USERNAME and DC_PASSWORD must be set for integration tests to run")
            self._dc = DeviceCloud(self._username, self._password, base_url=self._base_url)


def dc_inttest_main():
    """Helper method for kicking off integration tests in a module

    This is used in the same way that one might use 'unittest.main()' in a normal
    function.
    """
    os.environ["RUN_INTEGRATION_TESTS"] = "yes"
    if not os.environ.get("DC_USERNAME"):
        os.environ["DC_USERNAME"] = input("username: ")
    if not os.environ.get("DC_PASSWORD"):
        os.environ["DC_PASSWORD"] = getpass("password: ")
    unittest.main()
