# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
import pprint
import time
from devicecloud.streams import DataPoint

from devicecloud.test.integration.inttest_utilities import DeviceCloudIntegrationTestCase
import six


class StreamsIntegrationTestCase(DeviceCloudIntegrationTestCase):

    def test_event_reception(self):
        rx = []

        def receive_notification(notification):
            rx.append(notification)
            return True

        topics = ['DataPoint', 'FileData']
        monitor = self._dc.monitor.get_monitor(topics)
        if monitor:
            monitor.delete()
        monitor = self._dc.monitor.create_tcp_monitor(topics)
        monitor.add_callback(receive_notification)

        self._dc.filedata.write_file("/~/inttest/monitor_tcp/", "test_file.txt", six.b("Hello, world!"), "text/plain")
        self._dc.streams.get_stream("inttest/monitor_tcp").write(DataPoint(10))

        # Wait for the evenets to come in from the cloud
        time.sleep(3)
        self._dc.monitor.stop_listeners()

        try:
            fd_push_seen = False
            dp_push_seen = False
            for rec in rx:
                msg = rec['Document']['Msg']
                fd = msg.get('FileData', None)
                if fd:
                    if (fd['id']['fdName'] == 'test_file.txt' and
                            fd['id']['fdPath'] == '/db/7603_Etherios/inttest/monitor_tcp/'):
                        fd_push_seen = True
                dp = msg.get('DataPoint')
                if dp:
                    if dp['streamId'] == 'inttest/monitor_tcp':
                        dp_push_seen = True

            self.assertTrue(fd_push_seen)
            self.assertTrue(dp_push_seen)
        except:
            # add some additional debugging information
            pprint.pprint(rx)
            raise

if __name__ == '__main__':
    import unittest
    unittest.main()