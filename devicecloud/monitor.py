# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc. All rights reserved.
#
# This code is originally from another Digi Open Source Library:
# https://github.com/digidotcom/idigi-python-monitor-api
import xml.etree.ElementTree as ET
import logging
import textwrap
from devicecloud.apibase import APIBase
from devicecloud.conditions import Attribute
from devicecloud.monitor_tcp import TCPClientManager

logger = logging.getLogger(__name__)

#: System-generated identifier for the monitor.
MON_ID_ATTR = Attribute("monId")

#: Device Cloud customer identifier.
MON_CST_ID_ATTR = Attribute("cstId")

#: One or more topics to monitor separated by comma.  See the device cloud
#: documentation for more details
MON_TOPIC_ATTR = Attribute("monTopic")

#: Format for delivered event data: xml, json
MON_FORMAT_TYPE_ATTR = Attribute("monFormatType")

#: Transport method used to deliver push notifications to the
#: client application: tcp, http
MON_TRANSPORT_TYPE_ATTR = Attribute("monTransportType")

#: For HTTP transport type only. URL of the customer web server. For http URLs,
#: the default listening port is 80; for https URLs, the default listening
#: port is 443.
MON_HTTP_TRANSPORT_URL_ATTR = Attribute("monTransportUrl")

#: For HTTP transport type only. Credentials for basic authentication
#: in the following format: ``username:password``
MON_HTTP_TRANSPORT_TOKEN_ATTR = Attribute("monTransportToken")

#: For HTTP transport type only. HTTP method to use for sending
#: data: PUT or POST. The default is PUT.
MON_HTTP_TRANSPORT_METHOD_ATTR = Attribute("monTransportMethod")

#: For HTTP transport type only. Time in milliseconds Device Cloud waits
#: when attempting to connect to the destination http server. A value of
#: 0 means use the system default of 5000 (5 seconds). Most monitors do
#: not need to configure this setting.
MON_HTTP_CONNECT_TIMEOUT_ATTR = Attribute("monConnectTimeout")

#: For HTTP transport type only. Time in milliseconds Device Cloud waits
#: for a response for pushed events from the http server. A value of 0 means
#: use the system default of 5000 (5 seconds). Most monitors do not need to
#: configure this setting.
MON_HTTP_RESPONSE_TIMEOUT_ATTR = Attribute("monResponseTimeout")

#: For TCP transport type only. Indicates whether the client will explicitly
#: acknowledge TCP push events or allow Device Cloud to automatically acknowledge
#: events when sent. Options include: explicit or off. The default is off.
MON_TCP_ACK_OPTION_ATTR = Attribute("monAckOption")

#: Specifies an upper bound on how many messages are aggregated before sending
#: a batch. The default is 100.
MON_BATCH_SIZE_ATTR = Attribute("monBatchSize")

#: Specifies an upper bound on the number of seconds messages are aggregated
#: before sending. The default is 10.
MON_BATCH_DURATION_ATTR = Attribute("monBatchDuration")

#: Keyword that specifies the method used to compress messages. Options include:
#: zlib or none. The default is none. For zlib, the deflate algorithm is used to
#: compress the data; use inflate to decompress the data.
#:
#: Note: For backwards compatibility, gzip is accepted as a valid keyword.
#: Compression has always been done using the deflate algorithm.
MON_COMPRESSION_ATTR = Attribute("monCompression")

#: Boolean value that specifies whether Device Cloud replays any missed
#: published events before any new published events are forwarded. True
#: indicates missed published events are replayed. False indicates missed
#: published events are not replayed. The default is false.
MON_AUTO_REPLAY_ON_CONNECT = Attribute("monAutoReplayOnConnect")

#: Optional text field used to label or describe the monitor.
MON_DESCRIPTION_ATTR = Attribute("monDescription")

#: Specifies last connection time to the client application.
MON_LAST_CONNECT_ATTR = Attribute("monLastConnect")

#: Specifies the last message pushed to the client application
MON_LAST_SENT_ATTR = Attribute("monLastSent")

#: Specifies the current connection status to the client application:
#:
#: - CONNECTING: For HTTP monitors only. Device Cloud is attempting
#:     to connect to the configured HTTP server. Once connected, the state changes to ACTIVE.
#: - ACTIVE: Monitor is connected and publishing events.
#: - INACTIVE: Monitor is not connected and events are not published or recorded.
#: - SUSPENDED: For monitors with monAutoReplayOnConnect = True.  Monitor has disconnected,
#:     but publish events are recorded for later replay.
#: - DISABLED: For HTTP monitors only. If a monitor has not connected for 24 hours,
#:     the state is set to DISABLED, and publish events are not recorded for replay.
#:     A disabled monitor must be reconfigured via the Monitor web service.
MON_STATUS_ATTR = Attribute("monStatus")


class MonitorAPI(APIBase):
    """Provide access to the device cloud Monitor API for receiving push notifications

    The Monitor API in the device cloud allows for the creation and destruction of
    multiple "monitors."  Each monitor is registered against one or more "topics"
    which describe the data in which it is interested.

    There are, in turn, two main ways to receive data matching the topics for a
    given monitor:

    1. Stream: The device cloud supports a protocol over TCP (optionally with SSL) over which
       the batches of events will be sent when they are received.
    2. HTTP: When batches of events are received, a configured web
       service endpoint will received a POST request with the new data.

    Currently, this library supports setting up both types of monitors, but there
    is no special support provided for parsing HTTP postback requests.

    More information on the format for topic strings can be found in the `device
    cloud documentation for monitors <http://goo.gl/6UiOCG>`_.

    Here's a quick example showing a typical pattern used for creating a push monitor
    and associated listener that triggers a callback.  Deletion of existing monitors
    matching the same topics is not necessary but sometimes done in order to ensure
    that changes to the monitor configuration in code always make it to the monitor
    configuration in the device cloud::

        def monitor_callback(json_data):
            print(json_data)
            return True  # message received

        # Listen for DataPoint updates
        topics = ['DataPoint[U]']
        monitor = dc.monitor.get_monitor(topics)
        if monitor:
            monitor.delete()
        monitor = dc.monitor.create_tcp_monitor(topics)
        monitor.add_listener(monitor_callback)

        # later...
        dc.monitor.stop_listeners()

    When updates to any DataPoint in the device cloud occurs, the callback will be called
    with a data structure like this one::

        {'Document': {'Msg': {'DataPoint': {'cstId': 7603,
                                            'data': 0.411700824929,
                                            'description': '',
                                            'id': '684572e0-12c4-11e5-8507-fa163ed4cf14',
                                            'quality': 0,
                                            'serverTimestamp': 1434307047694,
                                            'streamId': 'test',
                                            'streamUnits': '',
                                            'timestamp': 1434307047694},
                                'group': '*',
                                'operation': 'INSERTION',
                                'timestamp': '2015-06-14T18:37:27.815Z',
                                'topic': '7603/DataPoint/test'}}}
    """

    def __init__(self, conn):
        APIBase.__init__(self, conn)
        # TODO: determine best way to expose additional options
        self._tcp_client_manager = TCPClientManager(self._conn, secure=True)

    def create_tcp_monitor(self, topics, batch_size=1, batch_duration=0,
                           compression='gzip', format_type='json'):
        """Creates a TCP Monitor instance in the device cloud for a given list of topics

        :param topics: a string list of topics (e.g. ['DeviceCore[U]',
                  'FileDataCore']).
        :param batch_size: How many Msgs received before sending data.
        :param batch_duration: How long to wait before sending batch if it
            does not exceed batch_size.
        :param compression: Compression value (i.e. 'gzip').
        :param format_type: What format server should send data in (i.e. 'xml' or 'json').

        Returns an object of the created Monitor
        """

        monitor_xml = """\
        <Monitor>
            <monTopic>{topics}</monTopic>
            <monBatchSize>{batch_size}</monBatchSize>
            <monFormatType>{format_type}</monFormatType>
            <monTransportType>tcp</monTransportType>
            <monCompression>{compression}</monCompression>
        </Monitor>
        """.format(
            topics=','.join(topics),
            batch_size=batch_size,
            batch_duration=batch_duration,
            format_type=format_type,
            compression=compression,
        )
        monitor_xml = textwrap.dedent(monitor_xml)

        response = self._conn.post("/ws/Monitor", monitor_xml)
        location = ET.fromstring(response.text).find('.//location').text
        monitor_id = int(location.split('/')[-1])
        return TCPDeviceCloudMonitor(self._conn, monitor_id, self._tcp_client_manager)

    def create_http_monitor(self, topics, transport_url, transport_token=None, transport_method='PUT',connect_timeout=0,
                            response_timeout=0, batch_size=1, batch_duration=0, compression='none', format_type='json'):
        """Creates a HTTP Monitor instance in the device cloud for a given list of topics

        :param topics: a string list of topics (e.g. ['DeviceCore[U]',
                  'FileDataCore']).
        :param transport_url: URL of the customer web server.
        :param transport_token: Credentials for basic authentication in the following format: username:password
        :param transport_method: HTTP method to use for sending data: PUT or POST. The default is PUT.
        :param connect_timeout: A value of 0 means use the system default of 5000 (5 seconds).
        :param response_timeout: A value of 0 means use the system default of 5000 (5 seconds).
        :param batch_size: How many Msgs received before sending data.
        :param batch_duration: How long to wait before sending batch if it
            does not exceed batch_size.
        :param compression: Compression value (i.e. 'gzip').
        :param format_type: What format server should send data in (i.e. 'xml' or 'json').

        Returns an object of the created Monitor
        """

        monitor_xml = """\
        <Monitor>
            <monTopic>{topics}</monTopic>
            <monBatchSize>{batch_size}</monBatchSize>
            <monFormatType>{format_type}</monFormatType>
            <monTransportType>http</monTransportType>
            <monTransportUrl>{transport_url}</monTransportUrl>
            <monTransportToken>{transport_token}</monTransportToken>
            <monTransportMethod>{transport_method}</monTransportMethod>
            <monConnectTimeout>{connect_timeout}</monConnectTimeout>
            <monResponseTimeout>{response_timeout}</monResponseTimeout>
            <monCompression>{compression}</monCompression>
        </Monitor>
        """.format(
            topics=','.join(topics),
            transport_url=transport_url,
            transport_token=transport_token,
            transport_method=transport_method,
            connect_timeout=connect_timeout,
            response_timeout=response_timeout,
            batch_size=batch_size,
            batch_duration=batch_duration,
            format_type=format_type,
            compression=compression,
        )
        monitor_xml = textwrap.dedent(monitor_xml)

        response = self._conn.post("/ws/Monitor", monitor_xml)
        location = ET.fromstring(response.text).find('.//location').text
        monitor_id = int(location.split('/')[-1])
        return HTTPDeviceCloudMonitor(self._conn, monitor_id)

    def get_monitors(self, condition=None, page_size=1000):
        """Return an iterator over all monitors matching the provided condition

        Get all inactive monitors and print id::

            for mon in dc.monitor.get_monitors(MON_STATUS_ATTR == "DISABLED"):
                print(mon.get_id())

        Get all the HTTP monitors and print id::

            for mon in dc.monitor.get_monitors(MON_TRANSPORT_TYPE_ATTR == "http"):
                print(mon.get_id())

        Many other possibilities exist.  See the :mod:`devicecloud.condition` documention
        for additional details on building compound expressions.

        :param condition: An :class:`.Expression` which defines the condition
            which must be matched on the monitor that will be retrieved from
            the device cloud. If a condition is unspecified, an iterator over
            all monitors for this account will be returned.
        :type condition: :class:`.Expression` or None
        :param int page_size: The number of results to fetch in a single page.
        :return: Generator yielding :class:`.DeviceCloudMonitor` instances matching the
            provided conditions.
        """
        req_kwargs = {}
        if condition:
            req_kwargs['condition'] = condition.compile()
        for monitor_data in self._conn.iter_json_pages("/ws/Monitor", **req_kwargs):
            yield DeviceCloudMonitor.from_json(self._conn, monitor_data, self._tcp_client_manager)

    def get_monitor(self, topics):
        """Attempts to find a Monitor in device cloud that matches the provided topics

        :param topics: a string list of topics (e.g. ``['DeviceCore[U]', 'FileDataCore'])``)

        Returns a :class:`DeviceCloudMonitor` if found, otherwise None.
        """
        for monitor in self.get_monitors(MON_TOPIC_ATTR == ",".join(topics)):
            return monitor  # return the first one, even if there are multiple
        return None

    def stop_listeners(self):
        """Stop any listener threads that may be running and join on them"""
        self._tcp_client_manager.stop()


class DeviceCloudMonitor(object):
    """Provides access to a single monitor instance on the device cloud

    This is a base class that should not be instantiated directly.

    :type _tcp_client_manager: devicecloud.monitor_tcp.TCPClientManager
    :type _conn: devicecloud.DeviceCloudConnection
    """

    # TODO: consider adding getters/setters for each metadata

    @classmethod
    def from_json(cls, conn, monitor_data, tcp_client_manager):
        monitor_id = int(monitor_data['monId'])
        transport_type = monitor_data['monTransportType']
        kls = {
            "tcp": TCPDeviceCloudMonitor,
            "http": HTTPDeviceCloudMonitor,
        }.get(transport_type.lower())
        if kls is None:
            raise ValueError("Unexpected monTransportType %r" % transport_type)
        return kls(conn, monitor_id, tcp_client_manager)

    def __init__(self, conn, monitor_id, *args, **kwargs):
        self._conn = conn
        self._id = monitor_id

    def get_id(self):
        """Get the ID of this monitor as an integer"""
        return self._id

    def get_metadata(self):
        """Get additional information about this monitor

        This method returns a dictionary where the keys contain information about the
        monitor.  The returned data will look something like this::

            {
                'cstId': '7603',
                'monBatchDuration': '10',
                'monBatchSize': '1',
                'monCompression': 'zlib',
                'monFormatType': 'json',
                'monId': '178023',
                'monStatus': 'INACTIVE',
                'monTopic': 'DeviceCore,FileDataCore,FileData,DataPoint',
                'monTransportType': 'tcp'
            }
        """
        return self._conn.get_json("/ws/Monitor/{id}".format(id=self._id))["items"][0]

    def delete(self):
        """Delete this monitor form the device cloud"""
        self._conn.delete("/ws/Monitor/{id}".format(id=self._id))

class HTTPDeviceCloudMonitor(DeviceCloudMonitor):
    """Device Cloud Monitor with HTTP transport type"""


class TCPDeviceCloudMonitor(DeviceCloudMonitor):
    """Device Cloud Monitor with TCP transport type"""

    def __init__(self, conn, monitor_id, tcp_client_manager):
        DeviceCloudMonitor.__init__(self, conn, monitor_id)
        self._tcp_client_manager = tcp_client_manager

    def add_callback(self, callback):
        """Create a secure SSL/TCP listen session to the device cloud"""
        self._tcp_client_manager.create_session(callback, self._id)
