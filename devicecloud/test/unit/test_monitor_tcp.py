# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.

from devicecloud.monitor_tcp import TCPClientManager
from devicecloud.test.unit.test_utilities import HttpTestBase


class TestTCPClientManager(HttpTestBase):

    # NOTE: currently only integration tests exist to test several parts of
    #   the basic device cloud push client functionality for historical reasons.
    #   In the future, it would be nice to extended the unit test coverage
    #   for this code.

    def setUp(self):
        HttpTestBase.setUp(self)
        self.client_manager = TCPClientManager(self.dc.get_connection())

    def test_hostname(self):
        self.assertEqual(self.client_manager.hostname, "login.etherios.com")

    def test_username(self):
        self.assertEqual(self.client_manager.username, "user")

    def test_password(self):
        self.assertEqual(self.client_manager.password, "pass")
