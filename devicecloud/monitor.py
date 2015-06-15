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
        monitor = dc.monitor.create_monitor(topics)
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

    def create_monitor(self, topics, batch_size=1, batch_duration=0, transport_type='tcp',
                       compression='gzip', format_type='json'):
        """Creates a Monitor instance in the device cloud for a given list of topics

        :param topics: a string list of topics (e.g. ['DeviceCore[U]',
                  'FileDataCore']).
        :param batch_size: How many Msgs received before sending data.
        :param batch_duration: How long to wait before sending batch if it
            does not exceed batch_size.
        :param transport_type: Either 'tcp' or 'http'
        :param compression: Compression value (i.e. 'gzip').
        :param format_type: What format server should send data in (i.e. 'xml' or 'json').

        Returns a string of the created Monitor Id (e.g.. 9001)
        """

        monitor_xml = """\
        <Monitor>
            <monTopic>{topics}</monTopic>
            <monBatchSize>{batch_size}</monBatchSize>
            <monFormatType>{format_type}</monFormatType>
            <monTransportType>{transport_type}</monTransportType>
            <monCompression>{compression}</monCompression>
        </Monitor>
        """.format(
            topics=','.join(topics),
            batch_size=batch_size,
            batch_duration=batch_duration,
            format_type=format_type,
            transport_type=transport_type,
            compression=compression,
        )
        monitor_xml = textwrap.dedent(monitor_xml)

        response = self._conn.post("/ws/Monitor", monitor_xml)
        location = ET.fromstring(response.text).find('.//location').text
        monitor_id = int(location.split('/')[-1])
        return DeviceCloudMonitor(self._conn, self._tcp_client_manager, monitor_id)

    def get_monitor(self, topics):
        """Attempts to find a Monitor in device cloud that matches the provided topics

        :param topics: a string list of topics (e.g. ``['DeviceCore[U]', 'FileDataCore'])``)

        Returns a :class:`DeviceCloudMonitor` if found, otherwise None.
        """
        condition = (Attribute("monTopic") == ",".join(topics))
        for monitor_data in self._conn.iter_json_pages("/ws/Monitor",
                                                       condition=condition.compile()):
            # just return the first one
            return DeviceCloudMonitor.from_json(self._conn, self._tcp_client_manager, monitor_data)
        return None

    def stop_listeners(self):
        """Stop any listener threads that may be running and join on them"""
        self._tcp_client_manager.stop()


class DeviceCloudMonitor(object):
    """Provides access to a single monitor instance on the device cloud

    :type _tcp_client_manager: devicecloud.monitor_tcp.TCPClientManager
    :type _conn: devicecloud.DeviceCloudConnection
    """

    # TODO: consider adding getters/setters for each metadata

    @classmethod
    def from_json(cls, conn, tcp_client_manager, monitor_data):
        monitor_id = int(monitor_data['monId'])
        return cls(conn, tcp_client_manager, monitor_id)

    def __init__(self, conn, tcp_client_manager, monitor_id):
        self._conn = conn
        self._tcp_client_manager = tcp_client_manager
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

    def add_listener(self, callback):
        """Create a secure SSL/TCP listen session to the device cloud"""
        self._tcp_client_manager.create_session(callback, self._id)
