# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015-2018 Digi International Inc. All rights reserved.

import unittest

from devicecloud.version import __version__


class TestVersion(unittest.TestCase):

    def test_version_format(self):
        self.assertTrue(len(__version__.split('.')) >= 3)
