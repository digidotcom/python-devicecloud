from apibase import APIBase
import logging

STREAM_TYPE_STRING = "string"
STREAM_TYPE_INT = "int"

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
   <dataTtl>{data_ttl}</dataTtl>
   <rollupTtl>{rollup_ttl}</rollupTtl>
</DataStream>
"""

logger = logging.getLogger("streams")


class StreamAPI(APIBase):
    def start_data_stream(self, name, data_type, data_ttl, rollup_ttl):
        data = DATA_STREAM_TEMPLATE.format(name=name,
                                           data_type=data_type,
                                           data_ttl=data_ttl,
                                           rollup_ttl=rollup_ttl)
        response = self._conn.post("/ws/DataStream", data)
        logger.info("Data stream created (%s) - HTTP(%s)", name, response.status_code)
        return response.content

    def stream_write(self, stream, data):
        data = DATA_POINT_TEMPLATE.format(data=data, stream=stream)
        response = self._conn.post("/ws/DataPoint", data)
        logger.info("Data sent (%s) to stream (%s) - HTTP(%s)", data, stream, response.status_code)
        return response.content

    def get_streams(self):
        return self._conn.get("/ws/DataStream")

    def get_stream_data(self, stream):
        return self._conn.get("/ws/DataPoint/%s" % stream)
