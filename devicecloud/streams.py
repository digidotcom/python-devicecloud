# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

"""Module providing classes for interacting with device cloud data streams


Data Streams on the device cloud provide a mechanism for storing time-series
values over a long period of time.  Each individual value in the time series
is known as a Data Point.

There are a few basic operations supported by the device cloud on streams which
are supported by the device cloud and this library.  Here we give examples of
each.

Creating a Stream
^^^^^^^^^^^^^^^^^

Streams can be created in two ways, both of which are supported by this library.

1. Create a stream explicitly using :py:meth:`~.StreamAPI.create_data_stream`
2. Write a data point to a stream that does not yet exist but include information key'
   to the stream using :py:meth:`~.StreamAPI.stream_write`.

Here's examples of these two methods for creating a new stream::

    from devicecloud import DeviceCloud
    from devicecloud.streams import Datapoint, STREAM_TYPE_FLOAT

    dc = DeviceCloud('user', 'pass')
    streams = dc.get_streams_api()

    # explicitly create a new data stream
    humidity_stream = streams.create_data_stream(
        stream_id="/%s/hudidity" % some_id,
        data_type="float",
        description="Humidity")
    humidity_stream.write(81.2)

    # create data stream implicitly
    temperature_stream = streams.get_stream("/%s/temperature" % some_id)
    temperature_stream.write(Datapoint(
            stream_id="/%s/temperature" % some_id,
            data=74.1,
            description="Outside Air Temperature in F",
            data_type=STREAM_TYPE_FLOAT,
            unit="Degrees Fahrenheit"
    ))

Getting Information About A Stream
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



"""

from StringIO import StringIO
import datetime
import logging

from devicecloud.apibase import APIBase
from devicecloud import DeviceCloudException, DeviceCloudHttpException
from devicecloud.util import iso8601_to_dt
from types import NoneType


DATA_POINT_TEMPLATE = """\
<DataPoint>
   <data>{data}</data>
   <streamId>{stream}</streamId>
</DataPoint>
"""

DATA_STREAM_TEMPLATE = """\
<DataStream>
   <streamId>{id}</streamId>
   <dataType>{data_type}</dataType>
   <description>{description}</description>
   <dataTtl>{data_ttl}</dataTtl>
   <rollupTtl>{rollup_ttl}</rollupTtl>
</DataStream>
"""

STREAM_TYPE_INTEGER = "INTEGER"
STREAM_TYPE_LONG = "LONG"
STREAM_TYPE_FLOAT = "FLOAT"
STREAM_TYPE_DOUBLE = "DOUBLE"
STREAM_TYPE_STRING = "STRING"
STREAM_TYPE_BINARY = "BINARY"
STREAM_TYPE_UNKNOWN = "UNKNOWN"

# Mapping in the following form:
# <dc-type> -> (<dc-to-python-fn>, <python-to-dc-fn>)
DSTREAM_TYPE_MAP = {
    STREAM_TYPE_INTEGER: (int, str),
    STREAM_TYPE_LONG: (int, str),
    STREAM_TYPE_FLOAT: (float, str),
    STREAM_TYPE_DOUBLE: (float, str),
    STREAM_TYPE_STRING: (str, str),
    STREAM_TYPE_BINARY: (str, str),
    STREAM_TYPE_UNKNOWN: (str, str),
}


ONE_DAY = 86400  # in seconds

logger = logging.getLogger("dc.streams")


#--- Helper Functions
def _validate_type(input, *types):
    if not isinstance(input, *types):
        raise TypeError("Input expected to one of following types: %s" % (types, ))
    return input


def _to_none_or_dt(input):
    """Convert string/None to None or a datetime object"""
    # if this is already None or a datetime, just use that
    if isinstance(input, (NoneType, datetime.datetime)):
        return input

    if isinstance(input, basestring):
        # try to convert from ISO8601
        try:
            return iso8601_to_dt(input)
        except ValueError:
            # finally, try unix... if this fails just-reraise ValueError
            unix_seconds = float(input)
            return datetime.datetime.fromtimestamp(unix_seconds)
    else:
        raise TypeError()


class StreamException(DeviceCloudException):
    """Base class for stream related exceptions"""


class NoSuchStreamException(StreamException):
    """Failure to find a stream based on a given id"""


class StreamAPI(APIBase):
    """Provide interface for interacting with device cloud streams API

    For further information, see :mod:`devicecloud.streams`.

    """

    def __init__(self, *args, **kwargs):
        APIBase.__init__(self, *args, **kwargs)
        self._streams_cache = {}  # mapping of streamId -> DataStream objects
        self._streams_cache_valid = False

    def _add_stream_to_cache(self, stream):
        self._streams_cache[stream.get_stream_id()] = stream

    def _get_streams(self, use_cached=True):
        """Clear and update internal cache of stream objects"""
        if not use_cached or not self._streams_cache_valid:
            self._streams_cache = {}
            response = self._conn.get_json("/ws/DataStream")
            for stream_data in response["items"]:
                stream_id = stream_data["streamId"]
                stream = DataStream(self._conn, stream_id, stream_data)
                self._streams_cache[stream_id] = stream
            self._streams_cache_valid = True
        return self._streams_cache

    def create_data_stream(self, stream_id, data_type, description=None, data_ttl=(ONE_DAY * 2),
                           rollup_ttl=(ONE_DAY * 5)):
        """Create and return a DataStream object"""
        description = description or ""

        data = DATA_STREAM_TEMPLATE.format(id=stream_id,
                                           description=description,
                                           data_type=data_type,
                                           data_ttl=data_ttl,
                                           rollup_ttl=rollup_ttl)

        self._conn.post("/ws/DataStream", data)
        logger.info("Data stream (%s) created successfully", stream_id)
        stream = DataStream(self._conn, stream_id)
        self._add_stream_to_cache(stream)
        return stream

    def get_streams(self, use_cached=True):
        """Return the list of all streams present on the device cloud

        :param use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :returns:  list of :class:`.DataStream` instances

        """
        return self._get_streams(use_cached).values()

    def get_stream(self, stream_id):
        """Return a reference to a stream with the given ``stream_id``

        Note that the requested stream may not exist yet.  If this is the
        case, later calls on the stream itself may fail.  To ensure that the
        stream exists, one can use :py:meth:`get_stream_if_exists` which will
        return None if the stream is not already created.

        :param stream_id: The path of the stream on the device cloud
        :raises: :class:`TypeError` if the stream_id provided is the wrong type
        :raises: :class:`ValueError` if the stream_id is not properly formed
        :returns: (:class:`.DataStream`) datastream instance with the provided stream_id

        """
        if self._streams_cache_valid:
            s = self._streams_cache.get(stream_id)
            if s is not None:
                return s

        return DataStream(self._conn, stream_id)

    def get_stream_if_exists(self, stream_id):
        """Return a reference to a stream with the given ``stream_id`` if it exists

        This works similar to :py:meth:`get_stream` but will return None if the
        stream is not already created.

        :param stream_id: The path of the stream on the device cloud
        :raises: :class:`TypeError` if the stream_id provided is the wrong type
        :raises: :class:`ValueError` if the stream_id is not properly formed
        :returns: (:class:`.DataStream`) :class:`.DataStream` instance with the provided stream_id

        """
        stream = self.get_stream(stream_id)
        try:
            stream.get_data_type(use_cached=True)
        except NoSuchStreamException:
            return None
        else:
            return stream


class DataPoint(object):
    """Encapsulate information about a single data point

    This class encapsulates the data required for both pushing data points to the
    device cloud as well as for storing and provding methods to access data from
    streams that has been retrieved from the device cloud.

    """

    @classmethod
    def from_json(cls, stream, json_data):
        """Create a new DataPoint object from device cloud JSON data

        :param stream: The :class:`~DataStream` out of which this data is coming
        :param json_data: Deserialized JSON data from the device cloud about this device
        :raises: ValueError if the data is malformed
        :returns: (:class:`~DataPoint`) newly created :class:`~DataPoint`

        """
        return cls(
            # these are actually properties of the stream, not the data point
            path=stream.get_stream_id(),
            data_type=stream.get_data_type(),
            unit=stream.get_unit(),

            # and these are part of the data point itself
            data=json_data.get("data"),
            description=json_data.get("description"),
            timestamp=iso8601_to_dt(json_data.get("timestampISO")),
            quality=json_data.get("quality"),
            location=json_data.get("location"),
        )

    def __init__(self, data, stream_id=None, description=None, timestamp=None,
                 quality=None, location=None, data_type=None, unit=None, dp_id=None,
                 customer_id=None, server_timestamp=None):
        self._stream_id = None  # invariant: always string or None
        self._data = None  # invariant: could be any type, with conversion applied lazily
        self._description = None  # invariant: always string or None
        self._timestamp = None  # invariant: always datetime object or None
        self._quality = None  # invariant: always integer (32-bit) or None
        self._location = None  # invariant: 3-tuple<float> or None
        self._data_type = None  # invariant: always string in set of types or None
        self._unit = None  # invariant: always string or None
        self._dp_id = None  # invariant: always string or None
        self._customer_id = None  # invariant: always string or None
        self._server_timestamp = None  # invariant: always None or datetime

        # all of these could be set via public API
        self.set_stream_id(stream_id)
        self.set_data(data)
        self.set_description(description)
        self.set_timestamp(timestamp)
        self.set_quality(quality)
        self.set_location(location)
        self.set_data_type(data_type)
        self.set_unit(unit)

        # these should only ever be read by the public API
        self._dp_id = _validate_type(dp_id, NoneType, basestring)
        self._customer_id = _validate_type(customer_id, NoneType, basestring)
        self._server_timestamp = _to_none_or_dt(server_timestamp)

    def get_id(self):
        """Get the ID of this data point if available

        The ID will only exist for data points retrieved from the data point and should
        not be set on data points that are being created.  This value is not designed
        to be set when creating data points.

        """
        return self._dp_id

    def get_data(self):
        """Get the actual data value associated with this data point"""
        data = self._data
        if self._data_type is not None:
            type_converters = DSTREAM_TYPE_MAP.get(self._data_type.upper())
            if type_converters:
                data = type_converters[0](self._data)
        return data

    def set_data(self, data):
        """Set the data for this data point

        This data may be converted upon access at a later point in time based
        on the data type of this stream (if set).

        """
        self._data = data

    def get_stream_id(self):
        """Get the stream ID for this data point if available"""
        return self._stream_id

    def set_stream_id(self, stream_id):
        """Set the stream id associated with this data point"""
        self._stream_id = _validate_type(stream_id, NoneType, basestring)

    def get_description(self):
        """Get the description associated with this data point if available"""
        return self._description

    def set_description(self, description):
        """Set the description for this data point"""
        self._description = _validate_type(description, NoneType, basestring)

    def get_timestamp(self):
        """Get the timestamp of this datapoint as a :class:`datetime.datetime` object

        This is the client assigned timestamp for this datapoint.  If this was not
        set by the client, it will be the same as the server timestamp.

        """
        return self._timestamp

    def set_timestamp(self, timestamp):
        """Set the timestamp for this data point

        The provided value should be either None, a datetime.datetime object, or a
        string with either ISO8601 or unix timestamp form.

        """
        self._timestamp = _to_none_or_dt(timestamp)

    def get_quality(self):
        """Get the quality as an integer

        This is a user-defined value whose meaning (if any) could vary per stream.  May
        not always be set.

        """
        return self._quality

    def set_quality(self, quality):
        """Set the quality for this sample

        Quality is stored on the device cloud as a 32-bit integer, so the input
        to this function should be either None, an integer, or a string that can
        be converted to an integer.

        """
        if isinstance(quality, basestring):
            quality = int(quality)
        elif isinstance(quality, float):
            quality = int(quality)

        self._quality = _validate_type(quality, NoneType, int, long)

    def get_location(self):
        """Get the location for this data point

        The location will be either None or a 3-tuple of floats in the form
        (latitude-degrees, longitude-degrees, altitude-meters).

        """
        return self._location

    def set_location(self, location):
        """Set the location for this data point

        The location must be either None (if no location data is known) or a
        3-tuple of floating point values in the form
        (latitude-degrees, longitude-degrees, altitude-meters).

        """
        if location is None:
            self._location = location

        if isinstance(location, basestring):  # from device cloud, convert from csv
            parts = map(float, str(location).split(","))
            if len(parts) == 3:
                self._location = tuple(map(float, parts))
            else:
                raise ValueError("Location string %r has unexpected format" % location)

        if (isinstance(location, tuple)
                and len(location) == 3
                and all([isinstance(x, float) for x in location])):
            self._location = location
        else:
            raise TypeError("Location must be None or 3-tuple of floats")

        self._location = location

    def set_data_type(self, data_type):
        """Set the data type for ths data point

        The data type is actually associated with the stream itself and should
        not (generally) vary on a point-per-point basis.  That being said, if
        creating a new stream by writing a datapoint, it may be beneficial to
        include this information.

        The data type provided should be in the set of available data types of
        { INTEGER, LONG, FLOAT, DOUBLE, STRING, BINARY, UNKNOWN }.

        """
        _validate_type(data_type, NoneType, basestring)
        if isinstance(data_type, basestring):
            data_type = str(data_type).upper()
        if not data_type in set([None] + DSTREAM_TYPE_MAP.keys()):
            raise ValueError("Provided data type not in available set of types")
        self._data_type = data_type

    def set_unit(self, unit):
        """Set the unit for this data point

        Unit, as with data_type, are actually associated with the stream and not
        the individual data point.  As such, changing this within a stream is
        not encouraged.  Setting the unit on the data point is useful when the
        stream might be created with the write of a data point.

        """
        self._unit = _validate_type(unit, NoneType, basestring)

    def to_xml(self):
        """Convert this datapoint into a form suitable for pushing to device cloud

        An XML string will be returned that will contain all pieces of information
        set on this datapoint.  Values not set (e.g. quality) will be ommitted.

        """
        out = StringIO()
        out.write("<DataPoint>")
        out.write("<streamId>%s</streamId>" % (self._stream_id[1:] if self._stream_id.startswith('/') else self._stream_id))
        out.write("<data>%s</data>" % self.get_data())
        if self._description is not None:
            out.write("<description>%s</description>" % self._description)
        if self._timestamp is not None:
            out.write("<timestamp>%s</timestamp>" % self._timestamp)
        if self._quality is not None:
            out.write("<quality>%s</quality>" % self._quality)
        if self._location is not None:
            out.write("<location>%s</location>" % self._location)
        if self._data_type:
            out.write("<streamType>%s</streamType>" % self._data_type)
        if self._unit:
            out.write("<streamUnits>%s</streamUnits>" % self._unit)
        out.write("</DataPoint>")
        return out.getvalue()


class DataStream(object):
    """Encapsulation of a DataStream's methods and attributes"""

    def __init__(self, conn, stream_id, cached_data=None):
        if not isinstance(cached_data, (NoneType, dict)):
            raise TypeError("cached_data should be dict or None")
        self._conn = conn
        self._stream_id = stream_id
        self._cached_data = cached_data

    def __repr__(self):
        return "DataStream(%s)" % (self._stream_id, )

    def _get_stream_metadata(self, use_cached):
        """Retrieve metadata about this stream from the device cloud"""
        if self._cached_data is None or not use_cached:
            try:
                self._cached_data = self._conn.get_json("/ws/DataStream/%s" % self._stream_id)["items"][0]
            except DeviceCloudHttpException, http_exception:
                if http_exception.response.status_code == 404:
                    raise NoSuchStreamException("Stream with id %r has not been created", self._stream_id)
                raise http_exception
        return self._cached_data

    def get_stream_id(self):
        """Get the id/path of this stream

        :returns: (strong) id/path of this stream

        """
        return self._stream_id

    def get_data_type(self, use_cached=True):
        """Get the data type of this stream if it exists

        The data type is the type of data stored in this data stream. Valid types include:

        * "INTEGER": data can be represented with a network (= big-endian) 32-bit two's-complement integer.  Data
             with this type maps to a python int.
        * "LONG": data can be represented with a network (= big-endian) 64-bit two's complement integer.  Data
             with this type maps to a python int.
        * "FLOAT": data can be represented with a network (= big-endian) 32-bit IEEE754 floating point.  Data
             with this type maps to a python float.
        * "DOUBLE": data can be represented with a network (= big-endian) 64-bit IEEE754 floating point.  Data
             with this type maps to a python float.
        * "STRING": UTF-8.  Data with this type map to a python string
        * "BINARY": Data with this type map to a python string.
        * "UNKNOWN": Data with this type map to a python string.

        :param use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :returns: (str) The data type of this stream as a string

        """
        dtype = self._get_stream_metadata(use_cached).get("dataType")
        if dtype is not None:
            dtype = dtype.upper()
        return dtype

    def get_description(self, use_cached=True):
        """Get the description associated with this data stream

        :param use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :raises: :class:`.DeviceCloudHttpException` in the case of an unexpected http error
        :raises: :class:`.NoSuchStreamException` if this stream has not yet been created
        :returns: (string) The description associated with this stream

        """
        return self._get_stream_metadata(use_cached).get("description")

    def get_data_ttl(self, use_cached=True):
        """Retrieve the dataTTL for this stream

        The dataTtl is the time to live (TTL) in seconds for data points stored in the data stream.
        A data point expires after the configured amount of time and is automatically deleted.

        :param use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :raises: :class:`.DeviceCloudHttpException` in the case of an unexpected http error
        :raises: :class:`.NoSuchStreamException` if this stream has not yet been created
        :returns: (int or None) The dataTtl associated with this stream in seconds

        """

        data_ttl_text = self._get_stream_metadata(use_cached).get("dataTtl")
        return int(data_ttl_text)

    def get_rollup_ttl(self, use_cached=True):
        """Retrieve the rollupTtl for this stream

        The rollupTtl is the time to live (TTL) in seconds for the aggregate roll-ups of data points
        stored in the stream. A roll-up expires after the configured amount of time and is
        automatically deleted.

        :param use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :raises: :class:`.DeviceCloudHttpException` in the case of an unexpected http error
        :raises: :class:`.NoSuchStreamException` if this stream has not yet been created
        :returns: (int or None) The rollupTtl associated with this stream in seconds
        """
        rollup_ttl_text = self._get_stream_metadata(use_cached).get("rollupTtl")
        return int(rollup_ttl_text)

    def get_current_value(self, use_cached=False):
        """Return the most recent DataPoint value written to a stream

        The current value is the last recorded data point for this stream.

        :param use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :raises: :class:`.DeviceCloudHttpException` in the case of an unexpected http error
        :raises: :class:`.NoSuchStreamException` if this stream has not yet been created
        :returns: (:class:`~DataPoint` or None) The most recent value written to this
            stream (or None if nothing has been written)

        """
        current_value = self._get_stream_metadata(use_cached).get("currentValue")
        if current_value:
            return DataPoint.from_json(self, current_value)
        else:
            return None

    def write_datapoint(self, datapoint):
        """Write some raw data to a stream using the DataPoint API

        This method will mutate the datapoint provided to populate it with information
        available from the stream as it is available (but without making any new HTTP
        requests).  For instance, we will add in information about the stream data
        type if it is available so that proper type conversion happens.

        Values already set on the datapoint will not be overridden (except for path)

        :param datapoint: The :class:`.DataPoint` that should be written to the device cloud

        """
        if not isinstance(datapoint, DataPoint):
            raise TypeError("First argument must be a DataPoint object")

        datapoint._stream_id = self.get_stream_id()
        if self._cached_data is not None and datapoint._data_type:
            datapoint._data_type = self.get_data_type()

        self._conn.post("/ws/DataPoint/%s" % self.get_stream_id(), datapoint.to_xml())

    def read(self):
        """Read one or more DataPoints from a stream"""

        # TODO: Implement me
