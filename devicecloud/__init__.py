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
    'DeviceCloudByEtherios',
    'DeviceCloudHttpException',
)

OK_RESPONSE_CODES = [
    200,
    201
]

ONE_DAY = 86400
HTTP_RETRIES = 3

logger = logging.getLogger("dc")


class DeviceCloudHttpException(Exception):
    """Exception raised when we failed a request to the DC over HTTP"""


def retryhttp(fn):
    """Decorator to aid with retrying an HTTP request

    The fn passed in here should return the response content or raise a
    DeviceCloudHttpException if there was an error.
    """
    def do_retries(*args, **kwargs):
        retries = HTTP_RETRIES
        while retries > 0:
            try:
                response = fn(*args, **kwargs)
                return response
            except DeviceCloudHttpException, e:
                logger.warn("DC HTTP Failure, retrying...")
                retries -= 1
                time.sleep(1)
        raise e
    return do_retries


class DeviceCloudConnection(object):
    def __init__(self, auth, base_url):
        self._auth = auth
        self._base_url = base_url

    def start(self):
        """Start and establish a Device Cloud connection

        Make sure that the login credentials are valid
        """
        # TODO: Implement me

    def _make_url(self, path):
        if not path.startswith("/"):
            path = "/" + path
        return "%s%s" % (self._base_url, path)

    @retryhttp
    def get(self, path, **kwargs):
        url = self._make_url(path)
        response = requests.get(url, auth=self._auth, **kwargs)
        if response.status_code == 200:
            return response.content
        else:
            err = "DC GET to %s failed - HTTP(%s)" % (path, response.status_code)
            raise DeviceCloudHttpException(err)

    @retryhttp
    def post(self, path, data, **kwargs):
        url = self._make_url(path)
        response = requests.post(url, data, auth=self._auth, **kwargs)
        if response.status_code in OK_RESPONSE_CODES:
            return response
        else:
            err = "DC POST to %s failed - HTTP(%s)" % (path, response.status_code)
            raise DeviceCloudHttpException(err)

    @retryhttp
    def put(self, path, data):
        url = self._make_url(path)
        response = requests.put(url, data, auth=self._auth)
        if response.status_code in OK_RESPONSE_CODES:
            return response
        else:
            err = "DC PUT to %s failed - HTTP(%s)" % (path, response.status_code)
            raise DeviceCloudHttpException(err)


class DeviceCloud(object):
    """Provides access to information/operations on a device cloud account"""

    def __init__(self, username, password, base_url="https://login.etherios.com"):
        self._conn = DeviceCloudConnection(HTTPBasicAuth(username, password), base_url)

        # Api Components
        self._file_data = FileDataAPI(self._conn)
        self._streams = StreamAPI(self._conn)
        self._sci = ServerCommandInterfaceAPI(self._conn)
        self._device_core = DeviceCoreAPI(self._conn, self._sci)

    #---------------------------------------------------------------------------
    # API - Streams
    #---------------------------------------------------------------------------
    def start_data_stream(self, name, data_type, data_ttl=(ONE_DAY * 2),
                                                 rollup_ttl=(ONE_DAY * 5)):
        """Open a data stream on the device cloud"""
        return self._streams.start_data_stream(name, data_type, data_ttl, rollup_ttl)

    def stream_write(self, stream, data):
        """Write a DataPoint to a previously opened DataStream"""
        self._streams.stream_write(stream, data)

    def get_streams(self):
        """Return a list of all available streams"""
        self._streams.get_streams()

    def get_stream_data(self, stream):
        """Return data from some stream"""
        self._streams.get_stream_data(stream)

    #---------------------------------------------------------------------------
    # API - FileData
    #---------------------------------------------------------------------------
    def fd_get_files(self, file_glob, device=None, from_date=None, contents=False):
        """Gets files that match the *file_glob* pattern using the FileData API

        If *device* is not ``None`` then it will only look for files from *device*.
        If *from_date* is not ``None`` then it will only for files modified since
        *from_date*. If *include_contents* is ``True`` then the file contents
        will be retrieved.
        """
        return self._file_data.get_files(file_glob, device, from_date, contents)

    def fd_put_file(self, file_name, file_data):
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
    def d_put_file(self):
        pass  # TODO: Implement me

    def d_get_file(self):
        pass  # TODO: Implement me

    #---------------------------------------------------------------------------
    # API - Monitors
    #---------------------------------------------------------------------------
    # TODO: Implement me

    #---------------------------------------------------------------------------
    # API - Alarms
    #---------------------------------------------------------------------------
    # TODO: Implement me
