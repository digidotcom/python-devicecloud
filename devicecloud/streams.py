# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.

r"""Module providing classes for interacting with device cloud data streams"""
import json
import logging
import datetime

import six
from devicecloud.apibase import APIBase
from devicecloud import DeviceCloudException, DeviceCloudHttpException
from devicecloud.util import conditional_write, to_none_or_dt, validate_type, isoformat, \
    dc_utc_timestamp_to_dt
from six import StringIO


urllib = six.moves.urllib

STREAM_TYPE_INTEGER = "INTEGER"
STREAM_TYPE_LONG = "LONG"
STREAM_TYPE_FLOAT = "FLOAT"
STREAM_TYPE_DOUBLE = "DOUBLE"
STREAM_TYPE_STRING = "STRING"
STREAM_TYPE_BINARY = "BINARY"
STREAM_TYPE_JSON = "JSON"
STREAM_TYPE_UNKNOWN = "UNKNOWN"

ROLLUP_INTERVAL_HALF = "half"
ROLLUP_INTERVAL_HOUR = "hour"
ROLLUP_INTERVAL_DAY = "day"
ROLLUP_INTERVAL_WEEK = "week"
ROLLUP_INTERVAL_MONTH = "month"

ROLLUP_METHOD_SUM = "sum"
ROLLUP_METHOD_AVERAGE = "average"
ROLLUP_METHOD_MIN = "min"
ROLLUP_METHOD_MAX = "max"
ROLLUP_METHOD_COUNT = "count"
ROLLUP_METHOD_STDDEV = "standarddev"

MAXIMUM_DATAPOINTS_PER_POST = 250


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
    STREAM_TYPE_JSON: (json.loads, json.dumps)
}


ONE_DAY = 86400  # in seconds

logger = logging.getLogger("devicecloud.streams")


def _get_encoder_method(stream_type):
    """A function to get the python type to device cloud type converter function.

    :param stream_type: The streams data type
    :return: A function that when called with the python object will return the serializable
    type for sending to the cloud. If there is no function for the given type, or the `stream_type`
    is `None` the returned function will simply return the object unchanged.
    """
    if stream_type is not None:
        return DSTREAM_TYPE_MAP.get(stream_type.upper(), (lambda x: x, lambda x: x))[1]
    else:
        return lambda x: x


def _get_decoder_method(stream_type):
    """ A function to get the device cloud type to python type converter function.

    :param stream_type: The streams data type
    :return: A function that when called with the device cloud object will return the python
    native type. If there is no function for the given type, or the `stream_type` is `None`
    the returned function will simply return the object unchanged.
    """
    if stream_type is not None:
        return DSTREAM_TYPE_MAP.get(stream_type.upper(), (lambda x: x, lambda x: x))[0]
    else:
        return lambda x: x


class StreamException(DeviceCloudException):
    """Base class for stream related exceptions"""


class NoSuchStreamException(StreamException):
    """Failure to find a stream based on a given id"""


class InvalidRollupDatatype(StreamException):
    """Roll-up's are only valid on numerical data types"""


class StreamsAPI(APIBase):
    """Provide interface for interacting with device cloud streams API

    For further information, see :mod:`devicecloud.streams`.

    """

    def __init__(self, *args, **kwargs):
        APIBase.__init__(self, *args, **kwargs)

    def _get_streams(self, uri_suffix=None):
        """Clear and update internal cache of stream objects"""
        # TODO: handle paging, perhaps change this to be a generator
        if uri_suffix is not None and not uri_suffix.startswith('/'):
            uri_suffix = '/' + uri_suffix
        elif uri_suffix is None:
            uri_suffix = ""
        streams = {}
        response = self._conn.get_json("/ws/DataStream{}".format(uri_suffix))
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
        description = validate_type(description, type(None), *six.string_types)
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

    def get_streams(self, stream_prefix=None):
        """Return the iterator over streams preset on device cloud.

        :param stream_prefix: An optional prefix to limit the iterator to; all streams are returned if it is not specified.

        :return:  iterator over all :class:`.DataStream` instances on the device cloud

        """
        # TODO: deal with paging.  We now return a generator, so the interface should look the same
        return iter(self._get_streams(stream_prefix).values())

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

    def bulk_write_datapoints(self, datapoints):
        """Perform a bulk write (or set of writes) of a collection of data points

        This method takes a list (or other iterable) of datapoints and writes them
        to the device cloud in an efficient manner, minimizing the number of HTTP
        requests that need to be made.

        As this call is performed from outside the context of any particular stream,
        each DataPoint object passed in must include information about the stream
        into which the point should be written.

        If all data points being written are for the same stream, you may want to
        consider using :meth:`~DataStream.bulk_write_datapoints` instead.

        Example::

            datapoints = []
            for i in range(300):
                datapoints.append(DataPoint(
                    stream_id="my/stream%d" % (i % 3),
                    data_type=STREAM_TYPE_INTEGER,
                    units="meters",
                    data=i,
                ))
            dc.streams.bulk_write_datapoints(datapoints)

        Depending on the size of the list of datapoints provided, this method may
        need to make multiple calls to the device cloud (in chunks of 250).

        :param list datapoints: a list of datapoints to be written to the device cloud
        :raises TypeError: if a list of datapoints is not provided
        :raises ValueError: if any of the provided data points do not have all required
            information (such as information about the stream)
        :raises DeviceCloudHttpException: in the case of an unexpected error in communicating
            with the device cloud.

        """
        datapoints = list(datapoints)  # effectively performs validation that we have the right type
        for dp in datapoints:
            if not isinstance(dp, DataPoint):
                raise TypeError("All items in the datapoints list must be DataPoints")
            if dp.get_stream_id() is None:
                raise ValueError("stream_id must be set on all datapoints")

        remaining_datapoints = datapoints
        while remaining_datapoints:
            # take up to 250 points and post them until complete
            this_chunk_of_datapoints = remaining_datapoints[:MAXIMUM_DATAPOINTS_PER_POST]
            remaining_datapoints = remaining_datapoints[MAXIMUM_DATAPOINTS_PER_POST:]

            # Build XML list containing data for all points
            datapoints_out = StringIO()
            datapoints_out.write("<list>")
            for dp in this_chunk_of_datapoints:
                datapoints_out.write(dp.to_xml())
            datapoints_out.write("</list>")

            # And send the HTTP Post
            self._conn.post("/ws/DataPoint", datapoints_out.getvalue())
            logger.info('DataPoint batch of %s datapoints written', len(this_chunk_of_datapoints))


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
        type_converter = _get_decoder_method(stream.get_data_type())
        data = type_converter(json_data.get("data"))
        return cls(
            # these are actually properties of the stream, not the data point
            stream_id=stream.get_stream_id(),
            data_type=stream.get_data_type(),
            units=stream.get_units(),

            # and these are part of the data point itself
            data=data,
            description=json_data.get("description"),
            timestamp=json_data.get("timestampISO"),
            server_timestamp=json_data.get("serverTimestampISO"),
            quality=json_data.get("quality"),
            location=json_data.get("location"),
            dp_id=json_data.get("id"),
        )

    @classmethod
    def from_rollup_json(cls, stream, json_data):
        """Rollup json data from the server looks slightly different

        :param DataStream stream: The :class:`~DataStream` out of which this data is coming
        :param dict json_data: Deserialized JSON data from the device cloud about this device
        :raises ValueError: if the data is malformed
        :return: (:class:`~DataPoint`) newly created :class:`~DataPoint`
        """
        dp = cls.from_json(stream, json_data)

        # Special handling for timestamp
        timestamp = isoformat(dc_utc_timestamp_to_dt(int(json_data.get("timestamp"))))

        # Special handling for data, all rollup data is float type
        type_converter = _get_decoder_method(stream.get_data_type())
        data = type_converter(float(json_data.get("data")))

        # Update the special fields
        dp.set_timestamp(timestamp)
        dp.set_data(data)
        return dp

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

    def __repr__(self):
        fmt = ("DataPoint(data={data!r}, "
               "stream_id={stream_id!r}, "
               "description={description!r}, "
               "timestamp={timestamp!r}, "
               "quality={quality!r}, "
               "location={location!r}, "
               "data_type={data_type!r}, "
               "units={units!r}, "
               "dp_id={dp_id!r}, "
               "customer_id={customer_id!r}, "
               "server_timestamp={server_timestamp!r})")
        return fmt.format(
            data=self.get_data(),
            stream_id=self.get_stream_id(),
            description=self.get_description(),
            timestamp=self.get_timestamp(),
            quality=self.get_quality(),
            location=self.get_location(),
            data_type=self.get_data_type(),
            units=self.get_units(),
            dp_id=self.get_id(),
            customer_id=self._customer_id,
            server_timestamp=self.get_server_timestamp()
        )

    def get_id(self):
        """Get the ID of this data point if available

        The ID will only exist for data points retrieved from the data point and should
        not be set on data points that are being created.  This value is not designed
        to be set when creating data points.

        """
        return self._dp_id

    def get_data(self):
        """Get the actual data value associated with this data point"""
        return self._data

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
            stream_id = stream_id.lstrip('/')
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
        type_converter = _get_encoder_method(self._data_type)
        # Convert from python native to device cloud
        encoded_data = type_converter(self._data)

        out = StringIO()
        out.write("<DataPoint>")
        out.write("<streamId>{}</streamId>".format(self.get_stream_id()))
        out.write("<data>{}</data>".format(encoded_data))
        conditional_write(out, "<description>{}</description>", self.get_description())
        if self.get_timestamp() is not None:
            out.write("<timestamp>{}</timestamp>".format(isoformat(self.get_timestamp())))
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

        stream_id = validate_type(stream_id, *six.string_types).lstrip('/')

        self._conn = conn
        self._stream_id = stream_id  # Invariant: string with any leading '/' stripped
        self._cached_data = cached_data

    def __repr__(self):
        # Provide a repr.  We want to avoid making an HTTP request here as that
        # might not be desirable
        if self._cached_data is None:
            return "DataStream(stream_id={stream_id!r})".format(
                stream_id=self.get_stream_id(),
            )
        else:
            # The purists will say that you should be able to eval this.  Realistically,
            # the idea behind a __repr__ is that it is unambiguous and above all useful
            # when debugging.  That is what we shoot for here.
            return ("DataStream(stream_id={stream_id!r}, "
                    "data_type={data_type!r}, "
                    "units={units!r}, "
                    "description={description!r}, "
                    "data_ttl={data_ttl!r}, "
                    "rollup_ttl={rollup_ttl!r})".format(
                stream_id=self.get_stream_id(),
                data_type=self.get_data_type(),
                units=self.get_units(),
                description=self.get_description(),
                data_ttl=self.get_data_ttl(),
                rollup_ttl=self.get_rollup_ttl(),
            ))

    def _get_stream_metadata(self, use_cached):
        """Retrieve metadata about this stream from the device cloud"""
        if self._cached_data is None or not use_cached:
            try:
                self._cached_data = self._conn.get_json("/ws/DataStream/%s" % self._stream_id)["items"][0]
            except DeviceCloudHttpException as http_exception:
                if http_exception.response.status_code == 404:
                    raise NoSuchStreamException("Stream with id %r has not been created" % self._stream_id)
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

    def delete_datapoint(self, datapoint):
        """Delete the provided datapoint from this stream

        :raises devicecloud.DeviceCloudHttpException: in the case of an unexpected http error

        """
        datapoint = validate_type(datapoint, DataPoint)
        self._conn.delete("/ws/DataPoint/{stream_id}/{datapoint_id}".format(
            stream_id=self.get_stream_id(),
            datapoint_id=datapoint.get_id(),
        ))

    def delete_datapoints_in_time_range(self, start_dt=None, end_dt=None):
        """Delete datapoints from this stream between the provided start and end times

        If neither a start or end time is specified, all data points in the stream
        will be deleted.

        :param start_dt: The datetime after which data points should be deleted or None
            if all data points from the beginning of time should be deleted.
        :param end_dt: The datetime before which data points should be deleted or None
            if all data points until the current time should be deleted.
        :raises devicecloud.DeviceCloudHttpException: in the case of an unexpected http error

        """
        start_dt = to_none_or_dt(validate_type(start_dt, datetime.datetime, type(None)))
        end_dt = to_none_or_dt(validate_type(end_dt, datetime.datetime, type(None)))

        params = {}
        if start_dt is not None:
            params['startTime'] = isoformat(start_dt)
        if end_dt is not None:
            params['endTime'] = isoformat(end_dt)

        self._conn.delete("/ws/DataPoint/{stream_id}{querystring}".format(
            stream_id=self.get_stream_id(),
            querystring="?" + urllib.parse.urlencode(params) if params else "",
        ))

    def bulk_write_datapoints(self, datapoints):
        """Perform a bulk write of a number of datapoints to this stream

        It is assumed that all datapoints here are to be written to this
        stream and the stream_id on each will be set by this method to
        this streams id (regardless of whether it is set or not).  To write multiple
        datapoints which span multiple streams, use :meth:`~StreamsAPI.bulk_write_endpoints`
        instead.

        :param list datapoints: A list of datapoints to be written into this stream

        """
        datapoints = list(datapoints)  # effectively performs validation that we have the right type
        for dp in datapoints:
            if not isinstance(dp, DataPoint):
                raise TypeError("All items in the datapoints list must be DataPoints")
            dp.set_stream_id(self.get_stream_id())

        # One could argue that this should just call out to StreamAPI.bulk_write_datapoints.  At
        # the time of writing, the stream has no reference back to StreamsAPI, so that is less
        # simple.
        remaining_datapoints = datapoints
        while remaining_datapoints:
            # take up to 250 points and post them until complete
            this_chunk_of_datapoints = remaining_datapoints[:MAXIMUM_DATAPOINTS_PER_POST]
            remaining_datapoints = remaining_datapoints[MAXIMUM_DATAPOINTS_PER_POST:]

            # Build XML list containing data for all points
            datapoints_out = StringIO()
            datapoints_out.write("<list>")
            for dp in this_chunk_of_datapoints:
                datapoints_out.write(dp.to_xml())
            datapoints_out.write("</list>")

            # And send the HTTP Post
            self._conn.post("/ws/DataPoint/{}".format(self.get_stream_id()), datapoints_out.getvalue())
            logger.info('DataPoint batch of %s datapoints written to stream %s',
                        len(this_chunk_of_datapoints), self.get_stream_id())

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

    def read(self, start_time=None, end_time=None, use_client_timeline=True, newest_first=True,
             rollup_interval=None, rollup_method=None, timezone=None, page_size=1000):
        """Read one or more DataPoints from a stream

        .. warning::
           The data points from the device cloud is a paged data set.  When iterating over the
           result set there could be delays when we hit the end of a page.  If this is undesirable,
           the caller should collect all results into a data structure first before iterating over
           the result set.

        :param start_time: The start time for the window of data points to read.  None means
            that we should start with the oldest data available.
        :type start_time: :class:`datetime.datetime` or None
        :param end_time: The end time for the window of data points to read.  None means
            that we should include all points received until this point in time.
        :type end_time: :class:`datetime.datetime` or None
        :param bool use_client_timeline: If True, the times used will be those provided by
              clients writing data points into the cloud (which also default to server time
              if the a timestamp was not included by the client).  This is usually what you
              want.  If False, the server timestamp will be used which records when the data
              point was received.
        :param bool newest_first: If True, results will be ordered from newest to oldest (descending order).
            If False, results will be returned oldest to newest.
        :param rollup_interval: the roll-up interval that should be used if one is desired at all.  Rollups
            will not be performed if None is specified for the interval.  Valid roll-up interval values
            are None, "half", "hourly", "day", "week", and "month".  See `DataPoints documentation
            <http://ftp1.digi.com/support/documentation/html/90002008/90002008_P/Default.htm#ProgrammingTopics/DataStreams.htm#DataPoints>`_
            for additional details on these values.
        :type rollup_interval: str or None
        :param rollup_method: The aggregation applied to values in the points within the specified
            rollup_interval.  Available methods are None, "sum", "average", "min", "max", "count", and
            "standarddev".  See `DataPoint documentation
            <http://ftp1.digi.com/support/documentation/html/90002008/90002008_P/Default.htm#ProgrammingTopics/DataStreams.htm#DataPoints>`_
            for additional details on these values.
        :type rollup_method: str or None
        :param timezone: timezone for calculating roll-ups. This determines roll-up interval
            boundaries and only applies to roll-ups of a day or larger (for example, day,
            week, or month). Note that it does not apply to the startTime and endTime parameters.
            See the `Timestamps <http://ftp1.digi.com/support/documentation/html/90002008/90002008_P/Default.htm#ProgrammingTopics/DataStreams.htm#timestamp>`_
            and `Supported Time Zones <http://ftp1.digi.com/support/documentation/html/90002008/90002008_P/Default.htm#ProgrammingTopics/DataStreams.htm#TimeZones>`_
            sections for more information.
        :type timezone: str or None
        :param int page_size: The number of results that we should attempt to retrieve from the
            device cloud in each page.  Generally, this can be left at its default value unless
            you have a good reason to change the parameter for performance reasons.
        :returns: A generator object which one can iterate over the DataPoints read.

        """

        is_rollup = False
        if (rollup_interval is not None) or (rollup_method is not None):
            is_rollup = True
            numeric_types = [
                STREAM_TYPE_INTEGER,
                STREAM_TYPE_LONG,
                STREAM_TYPE_FLOAT,
                STREAM_TYPE_DOUBLE,
                STREAM_TYPE_STRING,
                STREAM_TYPE_BINARY,
                STREAM_TYPE_UNKNOWN,
            ]

            if self.get_data_type(use_cached=True) not in numeric_types:
                raise InvalidRollupDatatype('Rollups only support numerical DataPoints')

        # Validate function inputs
        start_time = to_none_or_dt(validate_type(start_time, datetime.datetime, type(None)))
        end_time = to_none_or_dt(validate_type(end_time, datetime.datetime, type(None)))
        use_client_timeline = validate_type(use_client_timeline, bool)
        newest_first = validate_type(newest_first, bool)
        rollup_interval = validate_type(rollup_interval, type(None), *six.string_types)
        if not rollup_interval in {None,
                                   ROLLUP_INTERVAL_HALF,
                                   ROLLUP_INTERVAL_HOUR,
                                   ROLLUP_INTERVAL_DAY,
                                   ROLLUP_INTERVAL_WEEK,
                                   ROLLUP_INTERVAL_MONTH, }:
            raise ValueError("Invalid rollup_interval %r provided" % (rollup_interval, ))
        rollup_method = validate_type(rollup_method, type(None), *six.string_types)
        if not rollup_method in {None,
                                 ROLLUP_METHOD_SUM,
                                 ROLLUP_METHOD_AVERAGE,
                                 ROLLUP_METHOD_MIN,
                                 ROLLUP_METHOD_MAX,
                                 ROLLUP_METHOD_COUNT,
                                 ROLLUP_METHOD_STDDEV}:
            raise ValueError("Invalid rollup_method %r provided" % (rollup_method, ))
        timezone = validate_type(timezone, type(None), *six.string_types)
        page_size = validate_type(page_size, *six.integer_types)

        # Remember that there could be multiple pages of data and we want to provide
        # in iterator over the result set.  To start the process out, we need to make
        # an initial request without a page cursor.  We should get one in response to
        # our first request which we will use to page through the result set
        query_parameters = {
            'timeline': 'client' if use_client_timeline else 'server',
            'order': 'descending' if newest_first else 'ascending',
            'size': page_size
        }
        if start_time is not None:
            query_parameters["startTime"] = isoformat(start_time)
        if end_time is not None:
            query_parameters["endTime"] = isoformat(end_time)
        if rollup_interval is not None:
            query_parameters["rollupInterval"] = rollup_interval
        if rollup_method is not None:
            query_parameters["rollupMethod"] = rollup_method
        if timezone is not None:
            query_parameters["timezone"] = timezone

        result_size = page_size
        while result_size == page_size:
            # request the next page of data or first if pageCursor is not set as query param
            try:
                result = self._conn.get_json("/ws/DataPoint/{stream_id}?{query_params}".format(
                    stream_id=self.get_stream_id(),
                    query_params=urllib.parse.urlencode(query_parameters)
                ))
            except DeviceCloudHttpException as http_exception:
                if http_exception.response.status_code == 404:
                    raise NoSuchStreamException()
                raise http_exception

            result_size = int(result["resultSize"])  # how many are actually included here?
            query_parameters["pageCursor"] = result.get("pageCursor")  # will not be present if result set is empty
            for item_info in result.get("items", []):
                if is_rollup:
                    data_point = DataPoint.from_rollup_json(self, item_info)
                else:
                    data_point = DataPoint.from_json(self, item_info)
                yield data_point
