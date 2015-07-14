# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.

class APIBase(object):
    """Base class for all API Classes

    :type _conn: devicecloud.DeviceCloudConnection
    """
    def __init__(self, conn):
        self._conn = conn


class SCIAPIBase(object):
    """Base class for API classes using SCI to communicate

    :type _sci_api: devicecloud.sci.ServerCommandInterfaceAPI
    """
    def __init__(self, sci_api):
        self._sci_api = sci_api
