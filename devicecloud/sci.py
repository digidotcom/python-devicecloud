# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.

"""Server Command Interface functionality"""
from devicecloud.apibase import APIBase
from xml.etree import ElementTree as ET
import six


SCI_TEMPLATE = """\
<sci_request version="1.0">
  <{operation}{synchronous}{cache}{sync_timeout}{allow_offline}{wait_for_reconnect}>
    <targets>
      {targets}
    </targets>
    {payload}
  </{operation}>
</sci_request>
""".replace("  ", "").replace("\r", "").replace("\n", "")  # two spaces is indentation


class TargetABC(object):
    """Abstract base class for all target types"""


class DeviceTarget(TargetABC):
    """Target a specific device"""

    def __init__(self, device_id):
        self._device_id = device_id

    def to_xml(self):
        return '<device id="{}"/>'.format(self._device_id)


class AllTarget(TargetABC):
    """Target all devices"""

    def __init__(self):
        pass

    def to_xml(self):
        return '<device id="all"/>'


class TagTarget(TargetABC):
    """Target devices having a specific tag"""

    def __init__(self, tag):
        self._tag = tag

    def to_xml(self):
        return '<device tag="{}"/>'.format(self._tag)


class GroupTarget(TargetABC):
    """Target devices in a specific group"""

    def __init__(self, group):
        self._group = group

    def to_xml(self):
        return '<group path="{}">'.format(self._group)


class AsyncRequestProxy(object):
    """An object representing an asynychronous SCI request.

    Can be used for polling the status of the corresponding request.

    :ivar job_id: the ID in device cloud of the job
    :ivar response: the response to the request if completed
    :ivar completed: True if the request has completed, False otherwise; queries on read
    """
    def __init__(self, job_id, conn):
        self.job_id = job_id
        self._conn = conn
        self.response = None

    @property
    def completed(self):
        if self.response is not None:
            return True
        resp = self._conn.get('/ws/sci/{0}'.format(self.job_id))
        dom = ET.fromstring(resp.content)
        status = dom.find('.//status')
        if status is not None and status.text == 'complete':
            self.response = resp.content
            return True
        else:
            return False


class ServerCommandInterfaceAPI(APIBase):
    """Encapsulate Server Command Interface API"""

    def get_async_job(self, job_id):
        """Query an asynchronous SCI job by ID

        This is useful if the job was not created with send_sci_async().

        :param int job_id: The job ID to query
        :returns: The SCI response from GETting the job information
        """
        uri = "/ws/sci/{0}".format(job_id)
        # TODO: do parsing here?
        return self._conn.get(uri)

    def send_sci_async(self, operation, target, payload, **sci_options):
        """Send an asynchronous SCI request, and wraps the job in an object
        to manage it

        :param str operation: The operation is one of {send_message, update_firmware, disconnect, query_firmware_targets,
            file_system, data_service, and reboot}
        :param target: The device(s) to be targeted with this request
        :type target: :class:`~.TargetABC` or list of :class:`~.TargetABC` instances

        TODO: document other params

        """
        sci_options['synchronous'] = False
        resp = self.send_sci(operation, target, payload, **sci_options)
        dom = ET.fromstring(resp.content)
        job_element = dom.find('.//jobId')
        if job_element is None:
            return
        job_id = int(job_element.text)
        return AsyncRequestProxy(job_id, self._conn)

    def send_sci(self, operation, target, payload, reply=None, synchronous=None, sync_timeout=None,
                 cache=None, allow_offline=None, wait_for_reconnect=None):
        """Send SCI request to 1 or more targets

        :param str operation: The operation is one of {send_message, update_firmware, disconnect, query_firmware_targets,
            file_system, data_service, and reboot}
        :param target: The device(s) to be targeted with this request
        :type target: :class:`~.TargetABC` or list of :class:`~.TargetABC` instances

        TODO: document other params

        """
        if not isinstance(payload, six.string_types) and not isinstance(payload, six.binary_type):
            raise TypeError("payload is required to be a string or bytes")

        # validate targets and bulid targets xml section
        try:
            iter(target)
            targets = target
        except TypeError:
            targets = [target, ]
        if not all(isinstance(t, TargetABC) for t in targets):
            raise TypeError("Target(s) must each be instances of TargetABC")
        targets_xml = "".join(t.to_xml() for t in targets)

        # reply argument
        if not isinstance(reply, (type(None), six.string_types)):
            raise TypeError("reply must be either None or a string")
        if reply is not None:
            reply_xml = ' reply="{}"'.format(reply)
        else:
            reply_xml = ''

        # synchronous argument
        if not isinstance(synchronous, (type(None), bool)):
            raise TypeError("synchronous expected to be either None or a boolean")
        if synchronous is not None:
            synchronous_xml = ' synchronous="{}"'.format('true' if synchronous else 'false')
        else:
            synchronous_xml = ''

        # sync_timeout argument
        # TODO: What units is syncTimeout in?  seconds?
        if not sync_timeout is None or isinstance(sync_timeout, six.integer_types):
            raise TypeError("sync_timeout expected to either be None or a number")
        if sync_timeout is not None:
            sync_timeout_xml = ' syncTimeout="{}"'.format(sync_timeout)
        else:
            sync_timeout_xml = ''

        # cache argument
        if not isinstance(cache, (type(None), bool)):
            raise TypeError("cache expected to either be None or a boolean")
        if cache is not None:
            cache_xml = ' cache="{}"'.format('true' if cache else 'false')
        else:
            cache_xml = ''

        # allow_offline argument
        if not isinstance(allow_offline, (type(None), bool)):
            raise TypeError("allow_offline is expected to be either None or a boolean")
        if allow_offline is not None:
            allow_offline_xml = ' allowOffline="{}"'.format('true' if allow_offline else 'false')
        else:
            allow_offline_xml = ''

        # wait_for_reconnect argument
        if not isinstance(wait_for_reconnect, (type(None), bool)):
            raise TypeError("wait_for_reconnect expected to be either None or a boolean")
        if wait_for_reconnect is not None:
            wait_for_reconnect_xml = ' waitForReconnect="{}"'.format('true' if wait_for_reconnect else 'false')
        else:
            wait_for_reconnect_xml = ''

        full_request = SCI_TEMPLATE.format(
            operation=operation,
            targets=targets_xml,
            reply=reply_xml,
            synchronous=synchronous_xml,
            sync_timeout=sync_timeout_xml,
            cache=cache_xml,
            allow_offline=allow_offline_xml,
            wait_for_reconnect=wait_for_reconnect_xml,
            payload=payload
        )

        # TODO: do parsing here?
        return self._conn.post("/ws/sci", full_request)
