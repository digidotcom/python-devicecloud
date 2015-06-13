# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
import datetime

import arrow
from arrow.parser import DateTimeParser, ParserError
import six


def conditional_write(strm, fmt, value, *args, **kwargs):
    """Write to stream using fmt and value if value is not None"""
    if value is not None:
        strm.write(fmt.format(value, *args, **kwargs))


def iso8601_to_dt(iso8601):
    """Given an ISO8601 string as returned by the device cloud, convert to a datetime object"""
    # We could just use arrow.get() but that is more permissive than we actually want.
    # Internal (but still public) to arrow is the actual parser where we can be
    # a bit more specific
    parser = DateTimeParser()
    try:
        arrow_dt = arrow.Arrow.fromdatetime(parser.parse_iso(iso8601))
        return arrow_dt.to('utc').datetime
    except ParserError as pe:
        raise ValueError("Provided was not a valid ISO8601 string: %r" % pe)


def to_none_or_dt(input):
    """Convert ``input`` to either None or a datetime object

    If the input is None, None will be returned.
    If the input is a datetime object, it will be converted to a datetime
    object with UTC timezone info.  If the datetime object is naive, then
    this method will assume the object is specified according to UTC and
    not local or some other timezone.
    If the input to the function is a string, this method will attempt to
    parse the input as an ISO-8601 formatted string.

    :param input: Input data (expected to be either str, None, or datetime object)
    :return: datetime object from input or None if already None
    :rtype: datetime or None

    """
    if input is None:
        return input
    elif isinstance(input, datetime.datetime):
        arrow_dt = arrow.Arrow.fromdatetime(input, input.tzinfo or 'utc')
        return arrow_dt.to('utc').datetime
    if isinstance(input, six.string_types):
        # try to convert from ISO8601
        return iso8601_to_dt(input)
    else:
        raise TypeError("Not a string, NoneType, or datetime object")


def validate_type(input, *types):
    """Raise TypeError if the type of ``input`` is one of the args

    If the input value is one of the types specified, just return
    the input value.

    """
    if not isinstance(input, types):
        raise TypeError("Input expected to one of following types: %s" % (types, ))
    return input


def isoformat(dt):
    """Return an ISO-8601 formatted string from the provided datetime object"""
    if not isinstance(dt, datetime.datetime):
        raise TypeError("Must provide datetime.datetime object to isoformat")

    if dt.tzinfo is None:
        raise ValueError("naive datetime objects are not allowed beyond the library boundaries")

    return dt.isoformat().replace("+00:00", "Z")  # nicer to look at


def dc_utc_timestamp_to_dt(dc_timestamp_in_milleseconds):
    """Return a UTC datetime object"""
    return arrow.Arrow.utcfromtimestamp(dc_timestamp_in_milleseconds / 1000).datetime
