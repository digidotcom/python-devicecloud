# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

import datetime


def iso8601_to_dt(iso8601):
    """Given an ISO8601 string as returned by the device cloud, convert to a datetime object"""
    return datetime.datetime.strptime(iso8601, "%Y-%m-%dT%H:%M:%S.%fZ")
