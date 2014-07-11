# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

r"""Module providing classes for interacting with device cloud data streams"""

import logging
import six

from devicecloud.apibase import APIBase
from devicecloud import DeviceCloudException, DeviceCloudHttpException
from devicecloud.util import conditional_write, to_none_or_dt, validate_type
from six import StringIO


DATA_POINT_TEMPLATE = """\
<DataPoint>
   <data>{data}</data>
   <streamId>{stream}</streamId>
</DataPoint>
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

logger = logging.getLogger("devicecloud.streams")


class StreamException(DeviceCloudException):
    """Base class for stream related exceptions"""


class NoSuchStreamException(StreamException):
    """Failure to find a stream based on a given id"""


class StreamsAPI(APIBase):
    """Provide interface for interacting with device cloud streams API

    For further information, see :mod:`devicecloud.streams`.

    """

    def __init__(self, *args, **kwargs):
        APIBase.__init__(self, *args, **kwargs)

    def _get_streams(self):
        """Clear and update internal cache of stream objects"""
        # TODO: handle paging, perhaps change this to be a generator
        streams = {}
        response = self._conn.get_json("/ws/DataStream")
        for stream_data in response["items"]:
            stream_id = stream_data["streamId"]
            stream = DataStream(self._conn, stream_id, stream_data)
            streams[stream_id] = stream
        return streams

    def create_stream(self, stream_id, data_type, description=None, data_ttl=None,
                      rollup_ttl=None, units=None):
        """Create a new data stream on the device cloud

        This method will attempt to create a new data stream on the device cloud.
        This method will only succeed if the stream does not already exist.

        :param str stream_id: The path/id of the stream being created on the device cloud.
        :param str data_type: The type of this stream.  This must be in the set
            `{ INTEGER, LONG, FLOAT, DOUBLE, STRING, BINARY, UNKNOWN }`.  These values are
            available in constants like :attr:`~STREAM_TYPE_INTEGER`.
        :param str description: An optional description of this stream. See :meth:`~DataStream.get_description`.
        :param int data_ttl: The TTL for data points in this stream. See :meth:`~DataStream.get_data_ttl`.
        :param int rollup_ttl: The TTL for performing rollups on data. See :meth:~DataStream.get_rollup_ttl`.
        :param str units: Units for data in this stream.  See :meth:`~DataStream.get_units`

        """

        stream_id = validate_type(stream_id, *six.string_types)
        data_type = validate_type(data_type, type(None), *six.string_types)
        if isinstance(data_type, *six.string_types):
            data_type = str(data_type).upper()
        if not data_type in (set([None, ]) | set(list(DSTREAM_TYPE_MAP.keys()))):
            raise ValueError("data_type %r is not valid" % data_type)
        description = validate_type(stream_id, type(None), *six.string_types)
        data_ttl = validate_type(data_ttl, type(None), *six.integer_types)
        rollup_ttl = validate_type(rollup_ttl, type(None), *six.integer_types)
        units = validate_type(units, type(None), *six.string_types)

        sio = StringIO()
        sio.write("<DataStream>")
        conditional_write(sio, "<streamId>{}</streamId>", stream_id)
        conditional_write(sio, "<dataType>{}</dataType>", data_type)
        conditional_write(sio, "<description>{}</description>", description)
        conditional_write(sio, "<dataTtl>{}</dataTtl>", data_ttl)
        conditional_write(sio, "<rollupTtl>{}</rollupTtl>", rollup_ttl)
        conditional_write(sio, "<units>{}</units>", units)
        sio.write("</DataStream>")

        self._conn.post("/ws/DataStream", sio.getvalue())
        logger.info("Data stream (%s) created successfully", stream_id)
        stream = DataStream(self._conn, stream_id)
        return stream

    def get_streams(self):
        """Return the iterator over all streams present on the device cloud

        :return:  iterator over all :class:`.DataStream` instances on the device cloud

        """
        # TODO: deal with paging.  We now return a generator, so the interface should look the same
        return iter(self._get_streams().values())

    def get_stream(self, stream_id):
        """Return a reference to a stream with the given ``stream_id``

        Note that the requested stream may not exist yet.  If this is the
        case, later calls on the stream itself may fail.  To ensure that the
        stream exists, one can use :py:meth:`get_stream_if_exists` which will
        return None if the stream is not already created.

        :param stream_id: The path of the stream on the device cloud
        :raises TypeError: if the stream_id provided is the wrong type
        :raises ValueError: if the stream_id is not properly formed
        :return: datastream instance with the provided stream_id
        :rtype: DataStream

        """
        return DataStream(self._conn, stream_id)

    def get_stream_if_exists(self, stream_id):
        """Return a reference to a stream with the given ``stream_id`` if it exists

        This works similar to :py:meth:`get_stream` but will return None if the
        stream is not already created.

        :param stream_id: The path of the stream on the device cloud
        :raises TypeError: if the stream_id provided is the wrong type
        :raises ValueError: if the stream_id is not properly formed
        :return: :class:`.DataStream` instance with the provided stream_id
        :rtype: :class:`~DataStream`

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

        :param DataStream stream: The :class:`~DataStream` out of which this data is coming
        :param dict json_data: Deserialized JSON data from the device cloud about this device
        :raises ValueError: if the data is malformed
        :return: (:class:`~DataPoint`) newly created :class:`~DataPoint`

        """
        return cls(
            # these are actually properties of the stream, not the data point
            stream_id=stream.get_stream_id(),
            data_type=stream.get_data_type(),
            units=stream.get_units(),

            # and these are part of the data point itself
            data=json_data.get("data"),
            description=json_data.get("description"),
            timestamp=json_data.get("timestampISO"),
            server_timestamp=json_data.get("serverTimestampISO"),
            quality=json_data.get("quality"),
            location=json_data.get("location"),
            dp_id=json_data.get("id"),
        )

    def __init__(self, data, stream_id=None, description=None, timestamp=None,
                 quality=None, location=None, data_type=None, units=None, dp_id=None,
                 customer_id=None, server_timestamp=None):
        self._stream_id = None  # invariant: always string or None
        self._data = None  # invariant: could be any type, with conversion applied lazily
        self._description = None  # invariant: always string or None
        self._timestamp = None  # invariant: always datetime object or None
        self._quality = None  # invariant: always integer (32-bit) or None
        self._location = None  # invariant: 3-tuple<float> or None
        self._data_type = None  # invariant: always string in set of types or None
        self._units = None  # invariant: always string or None
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
        self.set_units(units)

        # these should only ever be read by the public API
        self._dp_id = validate_type(dp_id, type(None), *six.string_types)
        self._customer_id = validate_type(customer_id, type(None), *six.string_types)
        self._server_timestamp = to_none_or_dt(server_timestamp)

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
        stream_id = validate_type(stream_id, type(None), *six.string_types)
        if stream_id is not None:
            while stream_id.startswith('/'):
                stream_id = stream_id[1:]
        self._stream_id = stream_id

    def get_description(self):
        """Get the description associated with this data point if available"""
        return self._description

    def set_description(self, description):
        """Set the description for this data point"""
        self._description = validate_type(description, type(None), *six.string_types)

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
        self._timestamp = to_none_or_dt(timestamp)

    def get_server_timestamp(self):
        """Get the date and time at which the server received this data point"""
        return self._server_timestamp

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
        if isinstance(quality, *six.string_types):
            quality = int(quality)
        elif isinstance(quality, float):
            quality = int(quality)

        self._quality = validate_type(quality, type(None), *six.integer_types)

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

        elif isinstance(location, *six.string_types):  # from device cloud, convert from csv
            parts = str(location).split(",")
            if len(parts) == 3:
                self._location = tuple(map(float, parts))
                return
            else:
                raise ValueError("Location string %r has unexpected format" % location)

        # TODO: could maybe try to allow any iterable but this covers the most common cases
        elif (isinstance(location, (tuple, list))
                and len(location) == 3
                and all([isinstance(x, (float, six.integer_types)) for x in location])):
            self._location = tuple(map(float, location))  # coerce ints to float
        else:
            raise TypeError("Location must be None or 3-tuple of floats")

        self._location = location

    def get_data_type(self):
        """Get the data type for this data point

        The data type is associted with the stream itself but may also be
        included in data point writes.  The data type information in the point
        is also used to determine which type conversions should be applied to
        the data.

        """
        return self._data_type

    def set_data_type(self, data_type):
        """Set the data type for ths data point

        The data type is actually associated with the stream itself and should
        not (generally) vary on a point-per-point basis.  That being said, if
        creating a new stream by writing a datapoint, it may be beneficial to
        include this information.

        The data type provided should be in the set of available data types of
        { INTEGER, LONG, FLOAT, DOUBLE, STRING, BINARY, UNKNOWN }.

        """
        validate_type(data_type, type(None), *six.string_types)
        if isinstance(data_type, *six.string_types):
            data_type = str(data_type).upper()
        if not data_type in ({None} | set(DSTREAM_TYPE_MAP.keys())):
            raise ValueError("Provided data type not in available set of types")
        self._data_type = data_type

    def get_units(self):
        """Get the units of this datapoints stream if available"""
        return self._units

    def set_units(self, unit):
        """Set the unit for this data point

        Unit, as with data_type, are actually associated with the stream and not
        the individual data point.  As such, changing this within a stream is
        not encouraged.  Setting the unit on the data point is useful when the
        stream might be created with the write of a data point.

        """
        self._units = validate_type(unit, type(None), *six.string_types)

    def to_xml(self):
        """Convert this datapoint into a form suitable for pushing to device cloud

        An XML string will be returned that will contain all pieces of information
        set on this datapoint.  Values not set (e.g. quality) will be ommitted.

        """
        out = StringIO()
        out.write("<DataPoint>")
        out.write("<streamId>{}</streamId>".format(self.get_stream_id()))
        out.write("<data>{}</data>".format(self.get_data()))
        conditional_write(out, "<description>{}</description>", self.get_description())
        if self.get_timestamp() is not None:
            out.write("<timestamp>{}</timestamp>".format(self.get_timestamp().isoformat()))
        conditional_write(out, "<quality>{}</quality>", self.get_quality())
        if self.get_location() is not None:
            out.write("<location>%s</location>" % ",".join(map(str, self.get_location())))
        conditional_write(out, "<streamType>{}</streamType>", self.get_data_type())
        conditional_write(out, "<streamUnits>{}</streamUnits>", self.get_units())
        out.write("</DataPoint>")
        return out.getvalue()


class DataStream(object):
    """Encapsulation of a DataStream's methods and attributes"""

    # TODO: Add ability to modify stream metadata (e.g. set_data_ttl, etc.)

    def __init__(self, conn, stream_id, cached_data=None):
        if not isinstance(cached_data, (type(None), dict)):
            raise TypeError("cached_data should be dict or None")

        stream_id = validate_type(stream_id, *six.string_types)
        while stream_id.startswith("/"):
            stream_id = stream_id[1:]

        self._conn = conn
        self._stream_id = stream_id  # Invariant: string with any leading '/' stripped
        self._cached_data = cached_data

    def __repr__(self):
        return "DataStream(%r)" % (self._stream_id, )

    def _get_stream_metadata(self, use_cached):
        """Retrieve metadata about this stream from the device cloud"""
        if self._cached_data is None or not use_cached:
            try:
                self._cached_data = self._conn.get_json("/ws/DataStream/%s" % self._stream_id)["items"][0]
            except DeviceCloudHttpException as http_exception:
                if http_exception.response.status_code == 404:
                    raise NoSuchStreamException("Stream with id %r has not been created", self._stream_id)
                raise http_exception
        return self._cached_data

    def get_stream_id(self):
        """Get the id/path of this stream

        :return: id/path of this stream
        :rtype: str

        """
        return self._stream_id

    def get_data_type(self, use_cached=True):
        """Get the data type of this stream if it exists

        The data type is the type of data stored in this data stream. Valid types include:

        * INTEGER - data can be represented with a network (= big-endian) 32-bit two's-complement integer.  Data
          with this type maps to a python int.
        * LONG - data can be represented with a network (= big-endian) 64-bit two's complement integer.  Data
          with this type maps to a python int.
        * FLOAT - data can be represented with a network (= big-endian) 32-bit IEEE754 floating point.  Data
          with this type maps to a python float.
        * DOUBLE - data can be represented with a network (= big-endian) 64-bit IEEE754 floating point.  Data
          with this type maps to a python float.
        * STRING - UTF-8.  Data with this type map to a python string
        * BINARY - Data with this type map to a python string.
        * UNKNOWN - Data with this type map to a python string.

        :param bool use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :return: The data type of this stream as a string
        :rtype: str

        """
        dtype = self._get_stream_metadata(use_cached).get("dataType")
        if dtype is not None:
            dtype = dtype.upper()
        return dtype

    def get_units(self, use_cached=True):
        """Get the unit of this stream if it exists

        Units are a user-defined field stored as a string

        :param bool use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :return: The unit of this stream as a string
        :rtype: str or None

        """
        return self._get_stream_metadata(use_cached).get("units")

    def get_description(self, use_cached=True):
        """Get the description associated with this data stream

        :param bool use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :raises devicecloud.DeviceCloudHttpException: in the case of an unexpected http error
        :raises devicecloud.streams.NoSuchStreamException: if this stream has not yet been created
        :return: The description associated with this stream
        :rtype: str or None

        """
        return self._get_stream_metadata(use_cached).get("description")

    def get_data_ttl(self, use_cached=True):
        """Retrieve the dataTTL for this stream

        The dataTtl is the time to live (TTL) in seconds for data points stored in the data stream.
        A data point expires after the configured amount of time and is automatically deleted.

        :param bool use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :raises devicecloud.DeviceCloudHttpException: in the case of an unexpected http error
        :raises devicecloud.streams.NoSuchStreamException: if this stream has not yet been created
        :return: The dataTtl associated with this stream in seconds
        :rtype: int or None

        """

        data_ttl_text = self._get_stream_metadata(use_cached).get("dataTtl")
        return int(data_ttl_text)

    def get_rollup_ttl(self, use_cached=True):
        """Retrieve the rollupTtl for this stream

        The rollupTtl is the time to live (TTL) in seconds for the aggregate roll-ups of data points
        stored in the stream. A roll-up expires after the configured amount of time and is
        automatically deleted.

        :param bool use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :raises devicecloud.DeviceCloudHttpException: in the case of an unexpected http error
        :raises devicecloud.streams.NoSuchStreamException: if this stream has not yet been created
        :return: The rollupTtl associated with this stream in seconds
        :rtype: int or None

        """
        rollup_ttl_text = self._get_stream_metadata(use_cached).get("rollupTtl")
        return int(rollup_ttl_text)

    def get_current_value(self, use_cached=False):
        """Return the most recent DataPoint value written to a stream

        The current value is the last recorded data point for this stream.

        :param bool use_cached: If False, the function will always request the latest from the device cloud.
            If True, the device will not make a request if it already has cached data.
        :raises devicecloud.DeviceCloudHttpException: in the case of an unexpected http error
        :raises devicecloud.streams.NoSuchStreamException: if this stream has not yet been created
        :return: The most recent value written to this stream (or None if nothing has been written)
        :rtype: :class:`~DataPoint` or None

        """
        current_value = self._get_stream_metadata(use_cached).get("currentValue")
        if current_value:
            return DataPoint.from_json(self, current_value)
        else:
            return None

    def delete(self):
        """Delete this stream from the device cloud along with its history

        This call will return None on success and raise an exception in the event of an error
        performing the deletion.

        :raises devicecloud.DeviceCloudHttpException: in the case of an unexpected http error
        :raises devicecloud.streams.NoSuchStreamException: if this stream has already been deleted

        """
        try:
            self._conn.delete("/ws/DataStream/{}".format(self.get_stream_id()))
        except DeviceCloudHttpException as http_excpeption:
            if http_excpeption.response.status_code == 404:
                raise NoSuchStreamException()  # this branch is present, but the DC appears to just return 200 again
            else:
                raise http_excpeption

    def write(self, datapoint):
        """Write some raw data to a stream using the DataPoint API

        This method will mutate the datapoint provided to populate it with information
        available from the stream as it is available (but without making any new HTTP
        requests).  For instance, we will add in information about the stream data
        type if it is available so that proper type conversion happens.

        Values already set on the datapoint will not be overridden (except for path)

        :param DataPoint datapoint: The :class:`.DataPoint` that should be written to the device cloud

        """
        if not isinstance(datapoint, DataPoint):
            raise TypeError("First argument must be a DataPoint object")

        datapoint._stream_id = self.get_stream_id()
        if self._cached_data is not None and datapoint.get_data_type() is None:
            datapoint._data_type = self.get_data_type()

        self._conn.post("/ws/DataPoint/{}".format(self.get_stream_id()), datapoint.to_xml())

    def read(self):
        """Read one or more DataPoints from a stream"""
        # TODO: Implement me
