# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

import datetime
import six


def conditional_write(strm, fmt, value, *args, **kwargs):
    """Write to stream using fmt and value if value is not None"""
    if value is not None:
        strm.write(fmt.format(value, *args, **kwargs))


def iso8601_to_dt(iso8601):
    """Given an ISO8601 string as returned by the device cloud, convert to a datetime object"""
    return datetime.datetime.strptime(iso8601, "%Y-%m-%dT%H:%M:%S.%fZ")


def to_none_or_dt(input):
    """Convert string/None to None or a datetime object"""
    # if this is already None or a datetime, just use that
    if isinstance(input, (type(None), datetime.datetime)):
        return input

    if isinstance(input, six.string_types):
        # try to convert from ISO8601
        return iso8601_to_dt(input)
    else:
        raise TypeError("Not a string, NoneType, or datetime object")


def validate_type(input, *types):
    if not isinstance(input, types):
        raise TypeError("Input expected to one of following types: %s" % (types, ))
    return input