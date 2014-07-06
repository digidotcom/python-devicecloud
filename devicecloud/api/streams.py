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
            path="/%s/temperature" % some_id,
            data=74.1,
            description="Outside Air Temperature in F",
            data_type="FLOAT",
            unit="Deigrees Fahrenheit"
    ))

Getting Information About A Stream
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



"""

from StringIO import StringIO
from apibase import APIBase
import logging
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

ONE_DAY = 86400  # in seconds

logger = logging.getLogger("dc.streams")


class StreamException(DeviceCloudException):
    """Base class for stream related exceptions"""


class NoSuchStreamException(StreamException):
    """Failure to find a stream based on a given id"""


class StreamAPI(APIBase):
    """Provide interface for interacting with device cloud streams API

    For further information, see :mod:`devicecloud.api.streams`.

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

    def __init__(self, path, data, description=None, timestamp=None,
                 quality=None, location=None, data_type=None, unit=None):
        self.path = path
        self.data = data
        self.description = description
        self.timestamp = timestamp
        self.quality = quality
        self.location = location
        self.data_type = data_type
        self.unit = unit

    def to_xml(self):
        out = StringIO()
        out.write("<DataPoint>")
        out.write("<streamId>%s</streamId>" % (self.path[1:] if self.path.startswith('/') else self.path))
        out.write("<data>%s</data>" % self.data)
        if self.description is not None:
            out.write("<description>%s</description>" % self.description)
        if self.timestamp is not None:
            out.write("<timestamp>%s</timestamp>" % self.timestamp)
        if self.quality is not None:
            out.write("<quality>%s</quality>" % self.quality)
        if self.location is not None:
            out.write("<location>%s</location>" % self.location)
        if self.data_type:
            out.write("<streamType>%s</streamType>" % self.data_type)
        if self.unit:
            out.write("<streamUnits>%s</streamUnits>" % self.unit)
        out.write("</DataPoint>")
        return out.getvalue()


class DataStream(object):
    """Encapsulation of a DataStream's methods and attributes"""

    # Mapping in the following form:
    # <dc-type> -> (<dc-to-python-fn>, <python-to-dc-fn>)
    TYPE_MAP = {
        "integer": (int, str),
        "long": (int, str),
        "float": (float, str),
        "double": (float, str),
        "string": (str, str),
        "binary": (str, str),
        "unknown": (str, str),
    }

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

    def write(self, data):
        """Write some raw data to a stream using the DataPoint API

        Type checking/conversion will be applied here.

        """

        # TODO: Handle optional DataPoint arguments

        data = DATA_POINT_TEMPLATE.format(data=data, stream=self._stream_id)
        self._conn.post("/ws/DataPoint/%s" % self._stream_id, data)

    def read(self):
        """Read one or more DataPoints from a stream"""

        # TODO: Implement me
