from apibase import APIBase
from xml.etree import ElementTree
import logging

DATA_POINT_TEMPLATE = """\
<DataPoint>
   <data>{data}</data>
   <streamId>{stream}</streamId>
</DataPoint>
"""

DATA_STREAM_TEMPLATE = """\
<DataStream>
   <streamId>{name}</streamId>
   <dataType>{data_type}</dataType>
   <description>{description}</description>
   <dataTtl>{data_ttl}</dataTtl>
   <rollupTtl>{rollup_ttl}</rollupTtl>
</DataStream>
"""

logger = logging.getLogger("streams")


class StreamException(Exception):
    """Base class for stream related exceptions"""


class NoSuchStreamException(StreamException):
    """Failure to find a stream based on a given name"""


class StreamAPI(APIBase):
    """Stream class providing an interface to the Device Cloud streams API"""

    def __init__(self, *args, **kwargs):
        APIBase.__init__(self, *args, **kwargs)
        self._streams_cache = {}

    def start(self):
        self._load_streams()

    def _add_stream_to_cache(self, stream):
        self._streams_cache[stream.get_name()] = stream

    def _load_streams(self):
        """Clear and update internal cache of stream objects"""
        self._streams_cache = {}
        response = self._conn.get("/ws/DataStream")
        root = ElementTree.fromstring(response.content)
        for child in root:
            if child.tag == "DataStream":
                stream = DataStream.from_etree(child, self._conn)
                self._add_stream_to_cache(stream)

    def create_data_stream(self, name, data_type, description, data_ttl, rollup_ttl):
        """Create and return a DataStream object"""

        if not description:
            description = ""

        data = DATA_STREAM_TEMPLATE.format(name=name,
                                           description=description,
                                           data_type=data_type,
                                           data_ttl=data_ttl,
                                           rollup_ttl=rollup_ttl)

        self._conn.post("/ws/DataStream", data)
        logger.info("Data stream (%s) created successfully", name)
        stream = DataStream(name, data_type, description, data_ttl, rollup_ttl, self._conn)
        self._add_stream_to_cache(stream)
        return stream

    def get_streams(self, cached):
        """Return a cached (or not) list of available streams"""

        if not cached:
            self._load_streams()

        return self._streams_cache.values()

    def get_stream(self, name, cached):
        """Return a stream with a given `name` or None"""

        if not cached:
            self._load_streams()

        return self._streams_cache.get(name)

    def stream_write(self, stream_name, data):
        """If the stream exists, write some data to it using a DataPoint"""

        stream = self._streams_cache.get(stream_name)
        if stream:
            return stream.write(data)

        raise NoSuchStreamException("No stream with name %s", stream_name)

    def stream_read(self, stream_name):
        """If the stream exists, read one or more DataPoints from a stream"""

        stream = self._streams_cache.get(stream_name)
        if stream:
            return stream.read()

        raise NoSuchStreamException("No stream with name %s", stream_name)

    def delete_stream(self, stream_name):
        """Delete a DataStream with a given name"""
        self._conn.delete("/ws/DataStream/%s" % stream_name)


class DataStream(object):
    """Encapsulation of a DataStream's methods and attributes"""

    @classmethod
    def from_etree(cls, root, conn):
        name = root.find("streamId").text
        data_type = root.find("dataType").text.lower()
        description = root.find("description").text
        data_ttl = root.find("dataTtl").text
        rollup_ttl = root.find("rollupTtl").text
        return cls(name, data_type, description, data_ttl, rollup_ttl, conn)

    def __init__(self, name, data_type, description, data_ttl, rollup_ttl, conn):
        self._name = name
        self._description = description
        self._data_type = data_type
        self._data_ttl = data_ttl
        self._rollup_ttl = rollup_ttl
        self._conn = conn

    def __repr__(self):
        return "DataStream(%s, %s)" % (self._name, self._data_type)

    def get_name(self):
        return self._name

    def get_data_type(self):
        return self._data_type

    def get_description(self):
        return self._description

    def get_data_ttl(self):
        return self._data_ttl

    def get_rollup_ttl(self):
        return self._rollup_ttl

    def get_current_value(self):
        """Return the most recent DataPoint value written to a stream"""

        response = self._conn.get("/ws/DataStream/%s" % self._name)
        data_point = ElementTree.fromstring(response.content)
        current_value = data_point.find(".//currentValue")
        if current_value:
            return current_value.find(".//data").text
        else:
            return None

    def write(self, data):
        """Write some raw data to a stream using the DataPoint API

        Type checking/conversion will be applied here.
        """

        data = DATA_POINT_TEMPLATE.format(data=data, stream=self._name)
        self._conn.post("/ws/DataPoint/%s" % self._name, data)

    def read(self):
        """Read one or more DataPoints from a stream"""

        # TODO: Implement me
