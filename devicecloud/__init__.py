# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
import logging
import time
import json

from devicecloud.util import validate_type
from requests.auth import HTTPBasicAuth
import requests
from devicecloud.version import __version__
import six


__all__ = (
    'DeviceCloud',
    'DeviceCloudException',
    'DeviceCloudHttpException',
    'DeviceCloudConnection',
)

SUCCESSFUL_STATUS_CODES = [
    200,  # OK
    201,  # Created
    202,  # Accepted
    204,  # No Content (success for DELETE operation)
    207,  # Multi-Status (some success for provisioning, parse it before raising exception)
]

HTTP_THROTTLED_CODES = [
    429
]

# How long in seconds should we delay if a request is throttled?
#
# With a start of 1 second delay and a max of 10 and a default of 5 retries with a backoff coefficient
# of 1.5, then the backoff sequence will be the following:
#
#     1, 1.5, 2.25, 3.375, ~5
#
# With total delays of the following adding up at each period:
#
#     1, 2.5, 4.75, 8.125, 13.1875
#
# Assuming a 10s window, this will ensure that we hit a new window before the 5 retries
# are exhausted
DEFAULT_THROTTLE_RETRIES = 5
DEFAULT_THROTTLE_DELAY_INIT = 1.0
DEFAULT_THROTTLE_DELAY_MAX = 10.0
DEFAULT_THROTTLE_DELAY_BACKOFF_COEFFICIENT = 1.5

logger = logging.getLogger("devicecloud")


class DeviceCloudException(Exception):
    """Base class for Device Cloud Exceptions"""


class DeviceCloudHttpException(DeviceCloudException):
    """Exception raised when we failed a request to the DC over HTTP

    This exception will be raised whenever a non-success HTTP status
    code is received from the device cloud and there is no other logic
    in place for gracefully handling the error case.

    Often, if there is an error with a request to the device cloud, the device
    cloud will respond with an error status and include additional information
    about the nature of the error in the response body.  This information
    can be accessed via the :attr:`~response` property.

    """

    def __init__(self, response, *args, **kwargs):
        DeviceCloudException.__init__(self, *args, **kwargs)
        self._response = response

    def __str__(self):
        return "HTTP Status {code}: {content}".format(
            code=self.response.status_code,
            content=self.response.content
        )

    @property
    def response(self):
        """Get the requests response object for the failing HTTP request

        This object will be an instance of :class:`requests.Response` which
        in turn provides information including the content (body) of the response
        and the HTTP status code::

            try:
                dc.sci.send_request(...)
            except DeviceCloudHttpException as e:
                print "HTTP Error: %s" % e.response.status_code
                print e.response.content

        """
        return self._response


class DeviceCloudConnection(object):
    """Provide low-level access to the Device Cloud web services

    This is a convenience object that provides methods that make sending requests to the
    device cloud easier.  This object is used extensively within the library but can
    also be used externally (for instance, to support an API exposed by the device
    cloud that is not currently supported in the library).

    This object is accessible via :meth:`~DeviceCloud.get_connection`.

    """

    def __init__(self, auth, base_url,
                 throttle_retries=DEFAULT_THROTTLE_RETRIES,
                 throttle_delay_init=DEFAULT_THROTTLE_DELAY_INIT,
                 throttle_delay_max=DEFAULT_THROTTLE_DELAY_MAX,
                 throttle_delay_backoff_coefficient=DEFAULT_THROTTLE_DELAY_BACKOFF_COEFFICIENT):
        self._auth = auth
        self._base_url = base_url
        self._throttle_retries = throttle_retries
        self._throttle_delay_init = throttle_delay_init
        self._throttle_delay_max = throttle_delay_max
        self._throttle_delay_backoff_coefficient = throttle_delay_backoff_coefficient
        self._session = requests.Session()
        self._session.auth = auth

    @property
    def hostname(self):
        """Get the hostname that this connection is associated with"""
        from six.moves.urllib.parse import urlparse
        return urlparse(self._base_url).netloc.split(':', 1)[0]

    @property
    def username(self):
        return self._auth.username

    @property
    def password(self):
        return self._auth.password

    def _make_url(self, path):
        if not path.startswith("/"):
            path = "/" + path
        return "%s%s" % (self._base_url, path)

    def _make_request(self, method, url, **kwargs):
        #
        # Make a request, retrying up to 'retries' times backing off according to defined constants
        #
        throttle_retries = kwargs.pop('throttle_retries', kwargs.pop('retries', self._throttle_retries))
        throttle_delay_init = kwargs.pop('throttle_delay_init', self._throttle_delay_init)
        throttle_delay_max = kwargs.pop('throttle_delay_max', self._throttle_delay_max)
        throttle_delay_backoff_coefficient = \
            kwargs.pop('throttle_delay_backoff_coefficient', self._throttle_delay_backoff_coefficient)

        remaining_attempts = throttle_retries + 1
        retry_delay = throttle_delay_init
        while remaining_attempts > 0:
            response = self._session.request(method, url, **kwargs)
            if response.status_code in SUCCESSFUL_STATUS_CODES:
                return response
            elif response.status_code in HTTP_THROTTLED_CODES:
                remaining_attempts -= 1
                if remaining_attempts > 0:
                    logger.info("Request throttled on attempt {attempt}/{max_attempts}, retrying in {delay} seconds".format(
                        attempt=(throttle_retries + 1 - remaining_attempts),
                        max_attempts=throttle_retries,
                        delay=retry_delay
                    ))
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * throttle_delay_backoff_coefficient, throttle_delay_max)
            else:
                break

        err = "DC %s to %s failed - HTTP(%s)" % (method, url, response.status_code)
        raise DeviceCloudHttpException(response, err)

    def iter_json_pages(self, path, page_size=1000, **params):
        """Return an iterator over JSON items from a paginated resource

        Legacy resources (prior to V1) implemented a common paging interfaces for
        several different resources.  This method handles the details of iterating
        over the paged result set, yielding only the JSON data for each item
        within the aggregate resource.

        :param str path: The base path to the resource being requested (e.g. /ws/Group)
        :param int page_size: The number of items that should be requested for each page.  A larger
            page_size may mean fewer HTTP requests but could also increase the time to get a first
            result back from the device cloud.
        :param params: These are additional query parameters that should be sent with each
            request to the device cloud.

        """
        path = validate_type(path, *six.string_types)
        page_size = validate_type(page_size, *six.integer_types)

        offset = 0
        remaining_size = 1  # just needs to be non-zero
        while remaining_size > 0:
            reqparams = {"start": offset, "size": page_size}
            reqparams.update(params)
            response = self.get_json(path, params=reqparams)
            offset += page_size
            remaining_size = int(response.get("remainingSize", "0"))
            for item_json in response.get("items", []):
                yield item_json

    def ping(self):
        """Ping the Device Cloud using the authorization provided

        :return: The response of getting a single device from DeviceCore on success
        :raises: :class:`.DeviceCloudHttpException` if there is a problem

        """
        return self.get("/ws/DeviceCore?size=1")

    def get(self, path, **kwargs):
        """Perform an HTTP GET request of the specified path in the device cloud

        Make an HTTP GET request against the device cloud with this accounts
        credentials and base url.  This method uses the
        `requests <http://docs.python-requests.org/en/latest/>`_ library
        `request method <http://docs.python-requests.org/en/latest/api/#requests.request>`_
        and all keyword arguments will be passed on to that method.

        :param str path: The device cloud path to GET
        :param int retries: The number of times the request should be retried if an
            unsuccessful response is received.  Most likely, you should leave this at 0.
        :raises DeviceCloudHttpException: if a non-success response to the request is received
            from the device cloud
        :returns: A requests ``Response`` object

        """
        url = self._make_url(path)
        return self._make_request("GET", url, **kwargs)

    def get_json(self, path, **kwargs):
        """Perform an HTTP GET request with JSON headers of the specified path against the device cloud

        Make an HTTP GET request against the device cloud with this accounts
        credentials and base url.  This method uses the
        `requests <http://docs.python-requests.org/en/latest/>`_ library
        `request method <http://docs.python-requests.org/en/latest/api/#requests.request>`_
        and all keyword arguments will be passed on to that method.

        This method will automatically add the ``Accept: application/json`` and parse the
        JSON response from the device cloud.

        :param str path: The device cloud path to GET
        :param int retries: The number of times the request should be retried if an
            unsuccessful response is received.  Most likely, you should leave this at 0.
        :raises DeviceCloudHttpException: if a non-success response to the request is received
            from the device cloud
        :returns: A python data structure containing the results of calling ``json.loads`` on the
            body of the response from the device cloud.

        """

        url = self._make_url(path)
        headers = kwargs.setdefault('headers', {})
        headers.update({'Accept': 'application/json'})
        response = self._make_request("GET", url, **kwargs)
        return json.loads(response.text)

    def post(self, path, data, **kwargs):
        """Perform an HTTP POST request of the specified path in the device cloud

        Make an HTTP POST request against the device cloud with this accounts
        credentials and base url.  This method uses the
        `requests <http://docs.python-requests.org/en/latest/>`_ library
        `request method <http://docs.python-requests.org/en/latest/api/#requests.request>`_
        and all keyword arguments will be passed on to that method.

        :param str path: The device cloud path to POST
        :param int retries: The number of times the request should be retried if an
            unsuccessful response is received.  Most likely, you should leave this at 0.
        :param data: The data to be posted in the body of the POST request (see docs for
            ``requests.post``
        :raises DeviceCloudHttpException: if a non-success response to the request is received
            from the device cloud
        :returns: A requests ``Response`` object

        """
        url = self._make_url(path)
        return self._make_request("POST", url, data=data, **kwargs)

    def put(self, path, data, **kwargs):
        """Perform an HTTP PUT request of the specified path in the device cloud

        Make an HTTP PUT request against the device cloud with this accounts
        credentials and base url.  This method uses the
        `requests <http://docs.python-requests.org/en/latest/>`_ library
        `request method <http://docs.python-requests.org/en/latest/api/#requests.request>`_
        and all keyword arguments will be passed on to that method.

        :param str path: The device cloud path to PUT
        :param int retries: The number of times the request should be retried if an
            unsuccessful response is received.  Most likely, you should leave this at 0.
        :param data: The data to be posted in the body of the POST request (see docs for
            ``requests.post``
        :raises DeviceCloudHttpException: if a non-success response to the request is received
            from the device cloud
        :returns: A requests ``Response`` object

        """

        url = self._make_url(path)
        return self._make_request("PUT", url, data=data, **kwargs)

    def delete(self, path, retries=DEFAULT_THROTTLE_RETRIES, **kwargs):
        """Perform an HTTP DELETE request of the specified path in the device cloud

        Make an HTTP DELETE request against the device cloud with this accounts
        credentials and base url.  This method uses the
        `requests <http://docs.python-requests.org/en/latest/>`_ library
        `request method <http://docs.python-requests.org/en/latest/api/#requests.request>`_
        and all keyword arguments will be passed on to that method.

        :param str path: The device cloud path to DELETE
        :param int retries: The number of times the request should be retried if an
            unsuccessful response is received.  Most likely, you should leave this at 0.
        :raises DeviceCloudHttpException: if a non-success response to the request is received
            from the device cloud
        :returns: A requests ``Response`` object

        """
        url = self._make_url(path)
        return self._make_request("DELETE", url, **kwargs)


class DeviceCloud(object):
    """Provide access to core device cloud features

    This class is the primary interface to the device cloud through which access to individual
    device cloud services is provided.  Creating a ``DeviceCloud`` object is as easy as doing
    the following::

        from devicecloud import DeviceCloud

        dc = DeviceCloud('user', 'pass')
        if dc.has_valid_credentials():
            print list(dc.devicecore.get_devices())

    From there, access to all of the device clouds features are possible.  In some cases, methods
    for quickly performing selected actions may be provided directly via the ``DeviceCloud`` object
    while advanced usage requires using functionality exposed through other interfaces.

    """

    def __init__(self, username, password, base_url=None,
                 throttle_retries=DEFAULT_THROTTLE_RETRIES,
                 throttle_delay_init=DEFAULT_THROTTLE_DELAY_INIT,
                 throttle_delay_max=DEFAULT_THROTTLE_DELAY_MAX,
                 throttle_delay_backoff_coefficient=DEFAULT_THROTTLE_DELAY_BACKOFF_COEFFICIENT):
        if base_url is None:
            base_url = "https://login.etherios.com"
        self._conn = DeviceCloudConnection(
            auth=HTTPBasicAuth(username, password),
            base_url=base_url,
            throttle_retries=throttle_retries,
            throttle_delay_init=throttle_delay_init,
            throttle_delay_max=throttle_delay_max,
            throttle_delay_backoff_coefficient=throttle_delay_backoff_coefficient
        )
        self._streams_api = None  # streams property api ref
        self._filedata_api = None  # filedata property api ref
        self._devicecore_api = None  # devicecore property api ref
        self._sci_api = None  # sci property api ref
        self._monitor_api = None  # monitor property of api ref
        self._legacy_api = None  # legacy property api ref

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

    @property
    def file_system_service(self):
        """Property providing access to the :class:`.FileSystemServiceAPI`"""
        if self._fss_api is None:
            self._fss_api = self.get_fss_api()
        return self._fss_api

    @property
    def monitor(self):
        """Property providing access to the :class:`.MonitorAPI`"""
        if self._monitor_api is None:
            self._monitor_api = self.get_monitor_api()
        return self._monitor_api

    @property
    def ws(self):
        """Property providing access to the :class:`.WebServiceStub` with a base of ``/ws``"""
        return self.get_web_service_stub()

    def get_connection(self):
        """Get the low-level :class:`~DeviceCloudConnection` for this device cloud instance

        This object provides a low-level interface for making authenticated requests
        to the device cloud.

        """
        return self._conn

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

    def get_fss_api(self):
        """Returns a :class:`.FileSystemServiceAPI` bound to this device cloud instance

        This provides access to the same API as :attr:`.DeviceCloud.file_system_service` but will create
        a new object (with a new cache) each time called.

        :return: FSS API object bound to this device cloud account
        :rtype: :class:`.FileSystemServiceAPI`

        """
        from devicecloud.file_system_service import FileSystemServiceAPI

        return FileSystemServiceAPI(self.sci)

    def get_monitor_api(self):
        """Returns a :class:`.MonitorAPI` bound to this device cloud instance

        This provides access to the same API as :attr:`.DeviceCloud.monitor` but will create
        a new object (with a new cache) each time called.

        :return: Monitor API object bound to this device cloud account
        :rtype: :class:`.MonitorAPI`

        """
        from devicecloud.monitor import MonitorAPI

        return MonitorAPI(self._conn)

    def get_web_service_stub(self):
        """Returns a :class:`.WebServiceStub` bound to this device cloud instance

        This provides access to the same API as :attr:`.DeviceCloud.legacy` but will create
        a new object (with a new cache) each time called.

        :return: WebServiceStub object bound to this device cloud account with a base of ``/ws``
        :rtype: :class:`.WebServiceStub`

        """
        from devicecloud.ws import WebServiceStub

        return WebServiceStub(self._conn, "/ws")
