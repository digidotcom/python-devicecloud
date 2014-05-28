from devicecloud.api.sci import ServerCommandInterfaceAPI

__version__ = "0.1"

from devicecloud.api.devicecore import DeviceCoreAPI
from requests.auth import HTTPBasicAuth
from api.filedata import FileDataAPI
from api.streams import StreamAPI
import logging
import requests
import time

__all__ = (
    'DeviceCloud',
    'DeviceCloudException',
    'DeviceCloudHttpException',
)

ONE_DAY = 86400
HTTP_RETRIES = 3

logger = logging.getLogger("dc")


class DeviceCloudException(Exception):
    """Base class for Device Cloud Exceptions"""


class DeviceCloudHttpException(DeviceCloudException):
    """Exception raised when we failed a request to the DC over HTTP"""
    def __init__(self, response, *args, **kwargs):
        DeviceCloudException.__init__(self, *args, **kwargs)
        self.response = response


class _DeviceCloudConnection(object):
    SUCCESSFUL_STATUS_CODES = [
        200,
        201
    ]

    def __init__(self, auth, base_url):
        self._auth = auth
        self._base_url = base_url

    def start(self):
        """Establish/Verify a connection with the Device Cloud"""

        # Ping the device cloud, raises exception if it fails
        self.ping()

    def _make_url(self, path):
        if not path.startswith("/"):
            path = "/" + path
        return "%s%s" % (self._base_url, path)

    def _make_request(self, retries, method, url, **kwargs):
        remaining_attempts = retries + 1
        while remaining_attempts > 0:
            response = requests.request(method, url, auth=self._auth, **kwargs)
            if response.status_code in self.SUCCESSFUL_STATUS_CODES:
                return response
            remaining_attempts -= 1
            time.sleep(1)

        err = "DC %s to %s failed - HTTP(%s)" % (method, url, response.status_code)
        raise DeviceCloudHttpException(response, err)

    def ping(self):
        """Ping the Device Cloud using the authorization provided"""

    def get(self, path, retries=0, **kwargs):
        url = self._make_url(path)
        return self._make_request(retries, "GET", url, **kwargs)

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
    """Provides access to information/operations on a device cloud account"""

    def __init__(self, username, password, base_url="https://login.etherios.com"):
        self._conn = _DeviceCloudConnection(HTTPBasicAuth(username, password), base_url)

        # API Components
        self._file_data = FileDataAPI(self._conn)
        self._streams = StreamAPI(self._conn)
        self._sci = ServerCommandInterfaceAPI(self._conn)
        self._device_core = DeviceCoreAPI(self._conn, self._sci)

    def start(self):
        # Start connection, verifies credentials
        self._conn.start()

        # Start the API
        self._file_data.start()
        self._streams.start()
        self._sci.start()
        self._device_core.start()

    #---------------------------------------------------------------------------
    # API - Streams
    #---------------------------------------------------------------------------
    def create_data_stream(self, name, data_type, description=None,
                                                  data_ttl=(ONE_DAY * 2),
                                                  rollup_ttl=(ONE_DAY * 5)):
        """Create and return a DataStream object from the Device Cloud"""
        return self._streams.create_data_stream(name, data_type, description,
                                                data_ttl, rollup_ttl)

    def get_available_streams(self, cached=False):
        """Return a list of all available streams"""
        return self._streams.get_streams(cached)

    def get_stream(self, name, cached=False):
        return self._streams.get_stream(name, cached)

    def stream_write(self, stream, data):
        """Write a DataPoint to a previously opened DataStream"""
        self._streams.stream_write(stream, data)

    def stream_read(self, stream):
        """Return data from some stream"""
        return self._streams.stream_read(stream)

    #---------------------------------------------------------------------------
    # API - FileData
    #---------------------------------------------------------------------------
    def get_filedata_file(self, file_glob, device=None, from_date=None, contents=False):
        """Gets files that match the *file_glob* pattern using the FileData API

        If *device* is not ``None`` then it will only look for files from *device*.
        If *from_date* is not ``None`` then it will only for files modified since
        *from_date*. If *include_contents* is ``True`` then the file contents
        will be retrieved.
        """
        return self._file_data.get_files(file_glob, device, from_date, contents)

    def put_filedata_file(self, file_name, file_data):
        self._file_data.put_file(file_name, file_data)

    #---------------------------------------------------------------------------
    # API - DeviceCore
    #---------------------------------------------------------------------------
    def list_devices(self):
        """Get information about all devices associated with this device cloud account

        This method will return a list of :class:`.Device` instances.  Additional operations
        can be performed on these instances.

        """
        return self._device_core.list_devices()

    #---------------------------------------------------------------------------
    # API - Devices (SCI)
    #---------------------------------------------------------------------------
    def sci_put_file(self, addr, file_name, file_data):
        """Put a file onto the filesystem of a connected device"""
        raise NotImplementedError()

    def sci_get_file(self, addr, glob):
        """Get a file from the filesystem of a connected device"""
        raise NotImplementedError()

    #---------------------------------------------------------------------------
    # API - Monitors
    #---------------------------------------------------------------------------
    # TODO: Implement me

    #---------------------------------------------------------------------------
    # API - Alarms
    #---------------------------------------------------------------------------
    # TODO: Implement me
