# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from requests.auth import HTTPBasicAuth
import logging
import requests
import time
import json

from devicecloud.version import __version__

__all__ = (
    'DeviceCloud',
    'DeviceCloudException',
    'DeviceCloudHttpException',
)

SUCCESSFUL_STATUS_CODES = [
    200,  # OK
    201,  # Created
    202,  # Accepted
    204,  # No Content (success for DELETE operation)
]

logger = logging.getLogger("devicecloud")


class DeviceCloudException(Exception):
    """Base class for Device Cloud Exceptions"""


class DeviceCloudHttpException(DeviceCloudException):
    """Exception raised when we failed a request to the DC over HTTP"""

    def __init__(self, response, *args, **kwargs):
        DeviceCloudException.__init__(self, *args, **kwargs)
        self.response = response


class _DeviceCloudConnection(object):
    """Encapsulate information about a connection to the device cloud

    This class is used internally and does not represent a part of the public API
    to the device cloud.

    """

    def __init__(self, auth, base_url):
        self._auth = auth
        self._base_url = base_url

    def _make_url(self, path):
        if not path.startswith("/"):
            path = "/" + path
        return "%s%s" % (self._base_url, path)

    def _make_request(self, retries, method, url, **kwargs):
        remaining_attempts = retries + 1
        while remaining_attempts > 0:
            response = requests.request(method, url, auth=self._auth, **kwargs)
            if response.status_code in SUCCESSFUL_STATUS_CODES:
                return response
            remaining_attempts -= 1
            time.sleep(1)

        err = "DC %s to %s failed - HTTP(%s)" % (method, url, response.status_code)
        raise DeviceCloudHttpException(response, err)

    def ping(self):
        """Ping the Device Cloud using the authorization provided

        :return: The response of getting a single device from DeviceCore on success
        :raises: :class:`.DeviceCloudHttpException` if there is a problem

        """
        return self.get("/ws/DeviceCore?size=1")

    def get(self, path, retries=0, **kwargs):
        url = self._make_url(path)
        return self._make_request(retries, "GET", url, **kwargs)

    def get_json(self, path, retries=0, **kwargs):
        url = self._make_url(path)
        headers = kwargs.setdefault('headers', {})
        headers.update({'Accept': 'application/json'})
        response = self._make_request(retries, "GET", url, **kwargs)
        return json.loads(response.text)

    def post(self, path, data, retries=0, **kwargs):
        url = self._make_url(path)
        return self._make_request(retries, "POST", url, data=data, **kwargs)

    def put(self, path, data, retries=0, **kwargs):
        url = self._make_url(path)
        return self._make_request(retries, "PUT", url, data=data, **kwargs)

    def delete(self, path, retries=0):
        url = self._make_url(path)
        return self._make_request(retries, "DELETE", url)


class DeviceCloud(object):
    """Provide access to core device cloud features

    This class is the primary interface to the device cloud through which access to individual
    device cloud services is provided.  Creating a ``DeviceCloud`` object is as easy as doing
    the following::

        from devicecloud import DeviceCloud

        dc = DeviceCloud('user', 'pass')
        if dc.has_valid_credentials():
            print dc.devicecore.list_devices()

    From there, access to all of the device clouds features are possible.  In some cases, methods
    for quickly performing selected actions may be provided directly via the ``DeviceCloud`` object
    while advanced usage requires using functionality exposed through other interfaces.

    """

    def __init__(self, username, password, base_url="https://login.etherios.com"):
        self._conn = _DeviceCloudConnection(HTTPBasicAuth(username, password), base_url)
        self._streams_api = None  # streams property api ref
        self._filedata_api = None  # filedata property api ref
        self._devicecore_api = None  # devicecore property api ref
        self._sci_api = None  # sci property api ref

    def has_valid_credentials(self):
        """Verify that the device cloud url, username, and password are valid

        This method will attempt to "ping" the device cloud in order to ensure that all
        of the provided information is correct.

        :return: True if the credentials are valid and false if not
        :rtype: bool

        """
        try:
            self._conn.ping()
        except DeviceCloudException:
            return False
        else:
            return True

    @property
    def streams(self):
        """Property providing access to the :class:`.StreamsAPI`"""
        if self._streams_api is None:
            self._streams_api = self.get_streams_api()
        return self._streams_api

    @property
    def filedata(self):
        """Property providing access to the :class:`.FileDataAPI`"""
        if self._filedata_api is None:
            self._filedata_api = self.get_filedata_api()
        return self._filedata_api

    @property
    def devicecore(self):
        """Property providing access to the :class:`.DeviceCoreAPI`"""
        if self._devicecore_api is None:
            self._devicecore_api = self.get_devicecore_api()
        return self._devicecore_api

    @property
    def sci(self):
        """Property providing access to the :class:`.ServerCommandInterfaceAPI`"""
        if self._sci_api is None:
            self._sci_api = self.get_sci_api()
        return self._sci_api

    def get_streams_api(self):
        """Returns a :class:`.StreamsAPI` bound to this device cloud instance

        This provides access to the same API as :attr:`.DeviceCloud.streams` but will create
        a new object (with a new cache) each time called.

        :return: Stream API object bound to this device cloud account
        :rtype: :class:`.StreamsAPI`

        """
        from devicecloud.streams import StreamsAPI

        return StreamsAPI(self._conn)

    def get_filedata_api(self):
        """Returns a :class:`.FileDataAPI` bound to this device cloud instance

        This provides access to the same API as :attr:`.DeviceCloud.filedata` but will create
        a new object (with a new cache) each time called.

        :return: FileData API object bound to this device cloud account
        :rtype: :class:`.FileDataAPI`

        """
        from devicecloud.filedata import FileDataAPI  # prevent circular imports

        return FileDataAPI(self._conn)

    def get_devicecore_api(self):
        """Returns a :class:`.DeviceCoreAPI` bound to this device cloud instance

        This provides access to the same API as :attr:`.DeviceCloud.devicecore` but will create
        a new object (with a new cache) each time called.

        :return: devicecore API object bound to this device cloud account
        :rtype: :class:`.DeviceCoreAPI`

        """
        from devicecloud.devicecore import DeviceCoreAPI

        return DeviceCoreAPI(self._conn, self.get_sci_api())

    def get_sci_api(self):
        """Returns a :class:`.ServerCommandInterfaceAPI` bound to this device cloud instance

        This provides access to the same API as :attr:`.DeviceCloud.sci` but will create
        a new object (with a new cache) each time called.

        :return: SCI API object bound to this device cloud account
        :rtype: :class:`.ServerCommandInterfaceAPI`

        """
        from devicecloud.sci import ServerCommandInterfaceAPI

        return ServerCommandInterfaceAPI(self._conn)
