# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.

"""Provide access to the device cloud file system service API"""
import base64
from collections import namedtuple
import xml.etree.ElementTree as ET

from devicecloud.sci import DeviceTarget
import six
from devicecloud.apibase import SCIAPIBase


class FileSystemServiceException(Exception):
    """A file system service exception"""


class ResponseParseError(FileSystemServiceException):
    """An Exception when receiving an unexpected SCI response format"""


def _parse_command_response(response):
    """Parse an SCI command response into ElementTree XML

    This is a helper method that takes a Requests Response object
    of an SCI command response and will parse it into an ElementTree Element
    representing the root of the XML response.

    :param response: The requests response object
    :return: An ElementTree Element that is the root of the response XML
    :raises ResponseParseError: If the response XML is not well formed
    """
    try:
        root = ET.fromstring(response.text)
    except ET.ParseError:
        raise ResponseParseError(
            "Unexpected response format, could not parse XML. Response: {}".format(response.text))

    return root


def _parse_error_tree(error):
    """Parse an error ElementTree Node to create an ErrorInfo object

    :param error: The ElementTree error node
    :return: An ErrorInfo object containing the error ID and the message.
    """
    errinf = ErrorInfo(error.get('id'), None)
    if error.text is not None:
        errinf.message = error.text
    else:
        desc = error.find('./desc')
        if desc is not None:
            errinf.message = desc.text
    return errinf


class ErrorInfo(object):
    """Represents an error response from the device or the devicecloud

    :ivar errno: The error number reported in the response
    :ivar message: The error message reported in the response
    """

    def __init__(self, errno, message):
        self.errno = int(errno)
        self.message = message

    def __str__(self):
        return "<ErrorInfo errno:{errno} message:{message}>".format(errno=self.errno, message=self.message)


LsInfo = namedtuple('LsInfo', ['directories', 'files'])


class FileInfo(object):
    """Represents a file from a device

    This stores the information about a file on the device returned from an ls command.
    It also provides functionality to get the contents of the represented file and delete
    it.  However, writing to the file is not supported as it would invalidate the other
    information stored in this object.


    :param fssapi: A :class:`~.FileSystemServiceAPI` object to perform device file operations with
    :type fssapi: :class:`~.FileSystemServiceAPI`
    :param device_id: The Device ID of the device this file is on
    :param path: The path to this file on the device
    :param last_modified: The last time the file was modified
    :type last_modified: int
    :param size: The size of the file
    :type size: int
    :param hash: The files hash
    :param hash_type: The method used to produce the hash

    :ivar device_id: The Device ID of the device this file is on
    :ivar path: The path to this file on the device
    :ivar last_modified: The last time the file was modified
    :ivar size: The size of the file
    :ivar hash: The files hash
    :ivar hash_type: The method used to produce the hash
    """

    def __init__(self, fssapi, device_id, path, last_modified, size, hash, hash_type):
        self._fssapi = fssapi
        self.device_id = device_id
        self.path = path
        self.last_modified = last_modified
        self.size = size
        self.hash = hash
        self.hash_type = hash_type

    def get_data(self):
        """Get the contents of this file

        :return: The contents of this file
        :rtype: six.binary_type
        """

        target = DeviceTarget(self.device_id)
        return self._fssapi.get_file(target, self.path)[self.device_id]

    def delete(self):
        """Delete this file from the device

        .. note::
           After deleting the file, this object will no longer contain valid information
           and further calls to delete or get_data will return :class:`~.ErrorInfo` objects
        """
        target = DeviceTarget(self.device_id)
        return self._fssapi.delete_file(target, self.path)[self.device_id]

    def __str__(self):
        return "<FileInfo device:{device} path:{path}>".format(
            device=self.device_id,
            path=self.path
        )

    def __eq__(self, other):
        return (self.device_id == other.device_id and
                self.path == other.path and
                self.last_modified == other.last_modified and
                self.size == other.size and
                self.hash == other.hash)


class DirectoryInfo(object):
    """Represents a directory from a device

    This stores the information about a directory on the device returned from an ls command.
    It also provides functionality to list the contents of the directory.

    :param fssapi: A :class:`~.FileSystemServiceAPI` object to perform device directory operations with
    :type fssapi: :class:`~.FileSystemServiceAPI`
    :param device_id: The Device ID of the device this file is on
    :param path: The path to this file on the device
    :param last_modified: The last time the file was modified
    :type last_modified: int

    :ivar device_id: The Device ID of the device this file is on
    :ivar path: The path to this file on the device
    :ivar last_modified: the last time the file was modified
    """

    def __init__(self, fssapi, device_id, path, last_modified):
        self._fssapi = fssapi
        self.device_id = device_id
        self.path = path
        self.last_modified = last_modified

    def list_contents(self):
        """List the contents of this directory

        :return: A LsInfo object that contains directories and files
        :rtype: :class:`~.LsInfo` or :class:`~.ErrorInfo`

        Here is an example usage
        ::
            # let dirinfo be a DirectoryInfo object
            ldata = dirinfo.list_contents()
            if isinstance(ldata, ErrorInfo):
                # Do some error handling
                logger.warn("Error listing file info: (%s) %s", ldata.errno, ldata.message)
            # It's of type LsInfo
            else:
                # Look at all the files
                for finfo in ldata.files:
                    logger.info("Found file %s of size %s", finfo.path, finfo.size)
                # Look at all the directories
                for dinfo in ldata.directories:
                    logger.info("Found directory %s of last modified %s", dinfo.path, dinfo.last_modified)
        """
        target = DeviceTarget(self.device_id)
        return self._fssapi.list_files(target, self.path)[self.device_id]

    def __str__(self):
        return "<DirectoryInfo device:{device} path:{path}>".format(
            device=self.device_id,
            path=self.path,
        )

    def __eq__(self, other):
        return (self.device_id == other.device_id and
                self.path == other.path and
                self.last_modified == other.last_modified)


class FileSystemServiceAPI(SCIAPIBase):
    """ Encapsulate the File System Service API """

    def list_files(self, target, path, hash='any'):
        """List all files and directories in the path on the target

        :param target: The device(s) to be targeted with this request
        :type target: :class:`devicecloud.sci.TargetABC` or list of :class:`devicecloud.sci.TargetABC` instances
        :param path: The path on the target to list files and directories from
        :param hash: an optional attribute which indicates a hash over the file contents should be retrieved. Values
            include none, any, md5, and crc32. any is used to indicate the device should choose its best available hash.
        :return: A dictionary with keys of device ids and values of :class:`~.LsInfo` objects containing the files and
            directories or an :class:`~.ErrorInfo` object if there was an error response
        :raises: :class:`~.ResponseParseError` If the SCI response has unrecognized formatting

        Here is an example usage
        ::
            # dc is a DeviceCloud instance
            fssapi = dc.get_fss_api()

            target = AllTarget()
            ls_dir = '/root/home/user/important_files/'

            ls_data = fssapi.list_files(target, ls_dir)

            # Loop over all device results
            for device_id, device_data in ls_data.iteritems():
                # Check if it succeeded or was an error
                if isinstance(device_data, ErrorInfo):
                    # Do some error handling
                    logger.warn("Error listing file info on device %s. errno: %s message:%s",
                                device_id, device_data.errno, device_data.message)

                # It's of type LsInfo
                else:
                    # Look at all the files
                    for finfo in device_data.files:
                        logger.info("Found file %s of size %s on device %s",
                                    finfo.path, finfo.size, device_id)
                    # Look at all the directories
                    for dinfo in device_data.directories:
                        logger.info("Found directory %s of last modified %s on device %s",
                                    dinfo.path, dinfo.last_modified, device_id)

        """
        commands_el = ET.Element('commands')
        ls_el = ET.SubElement(commands_el, 'ls')
        ls_el.set('path', path)
        ls_el.set('hash', hash)
        root = _parse_command_response(
            self._sci_api.send_sci("file_system", target, ET.tostring(commands_el)))

        out_dict = {}

        #  At this point the XML we have is of the form
        # <sci_reply>
        #   <file_system>
        #     <device id="device_id">
        #       <commands>
        #         <ls hash="hash_type">
        #           <file path="file_path" last_modified=last_modified_time ... />
        #           ...
        #           <dir path="dir_path" last_modified=last_modified_time />
        #           ...
        #         </ls>
        #       </commands>
        #     </device>
        #     <device id="device_id">
        #       <commands>
        #         <ls hash="hash_type">
        #           <file path="file_path" last_modified=last_modified_time ... />
        #           ...
        #           <dir path="dir_path" last_modified=last_modified_time />
        #           ...
        #         </ls>
        #       </commands>
        #     </device>
        #     ...
        #   </file_system>
        # </sci_reply>

        # Here we will get each of the XML trees rooted at the device nodes
        for device in root.findall('./file_system/device'):
            device_id = device.get('id')
            error = device.find('.//error')
            if error is not None:
                out_dict[device_id] = _parse_error_tree(error)
            else:
                hash_type = device.find('./commands/ls').get('hash')
                dirs = []
                files = []
                # Get each file listed for this device
                for myfile in device.findall('./commands/ls/file'):
                    fi = FileInfo(self,
                                  device_id,
                                  myfile.get('path'),
                                  int(myfile.get('last_modified')),
                                  int(myfile.get('size')),
                                  myfile.get('hash'),
                                  hash_type)
                    files.append(fi)
                # Get each directory listed for this device
                for mydir in device.findall('./commands/ls/dir'):
                    di = DirectoryInfo(self,
                                       device_id,
                                       mydir.get('path'),
                                       int(mydir.get('last_modified')))
                    dirs.append(di)
                out_dict[device_id] = LsInfo(directories=dirs, files=files)
        return out_dict

    def get_file(self, target, path, offset=None, length=None):
        """Get the contents of a file on the device

        :param target: The device(s) to be targeted with this request
        :type target: :class:`devicecloud.sci.TargetABC` or list of :class:`devicecloud.sci.TargetABC` instances
        :param path: The path on the target to the file to retrieve
        :param offset: Start retrieving data from this byte position in the file, if None start from the beginning
        :param length: How many bytes to retrieve, if None retrieve until the end of the file
        :return: A dictionary with keys of device ids and values of the bytes of the file (or partial file if offset
            and/or length are specified) or an :class:`~.ErrorInfo` object if there was an error response
        :raises: :class:`~.ResponseParseError` If the SCI response has unrecognized formatting
        """
        commands_el = ET.Element('commands')
        get_file_el = ET.SubElement(commands_el, 'get_file')
        get_file_el.set('path', path)
        if offset is not None:
            get_file_el.set('offset', str(offset))
        if length is not None:
            get_file_el.set('length', str(length))

        root = _parse_command_response(
            self._sci_api.send_sci("file_system", target, ET.tostring(commands_el)))
        out_dict = {}
        for device in root.findall('./file_system/device'):
            device_id = device.get('id')
            error = device.find('.//error')
            if error is not None:
                out_dict[device_id] = _parse_error_tree(error)
            else:
                data = six.b(device.find('./commands/get_file/data').text)
                out_dict[device_id] = base64.b64decode(data)
        return out_dict

    def put_file(self, target, path, file_data=None, server_file=None, offset=None, truncate=False):
        """Put data into a file on the device

        :param target: The device(s) to be targeted with this request
        :type target: :class:`devicecloud.sci.TargetABC` or list of :class:`devicecloud.sci.TargetABC` instances
        :param path: The path on the target to the file to write to.  If the file already exists it will be overwritten.
        :param file_data: A `six.binary_type` containing the data to put into the file
        :param server_file: The path to a file on the devicecloud server containing the data to put into the file on the
            device
        :param offset: Start writing bytes to the file at this position, if None start at the beginning
        :param truncate: Boolean, if True after bytes are done being written end the file their even if previous data
            exists beyond it.  If False, leave any existing data in place.
        :return: A dictionary with keys being device ids and value being None if successful or an :class:`~.ErrorInfo`
            if the operation failed on that device
        :raises: :class:`~.FileSystemServiceException` if either both file_data and server_file are specified or
            neither are specified
        :raises: :class:`~.ResponseParseError` If the SCI response has unrecognized formatting
        """
        if file_data is not None and server_file is not None:
            raise FileSystemServiceException("Can only specify one of server_file or file_data")

        commands_el = ET.Element('commands')
        put_file_el = ET.SubElement(commands_el, 'put_file')
        put_file_el.set('path', path)
        put_file_el.set('truncate', 'true' if truncate else 'false')

        if offset is not None:
            put_file_el.set('offset', str(offset))

        if file_data is not None:
            if not isinstance(file_data, six.binary_type):
                raise TypeError("file_data must be of type {}".format(six.binary_type))
            data_el = ET.SubElement(put_file_el, 'data')
            data_el.text = base64.b64encode(file_data).decode('ascii')
        elif server_file is not None:
            file_el = ET.SubElement(put_file_el, 'file')
            file_el.text = server_file
        else:
            raise FileSystemServiceException("You must specify either file_data or server_file to put data into a file")

        root = _parse_command_response(self._sci_api.send_sci("file_system", target, ET.tostring(commands_el)))
        out_dict = {}
        for device in root.findall('./file_system/device'):
            device_id = device.get('id')
            error = device.find('.//error')
            if error is not None:
                out_dict[device_id] = _parse_error_tree(error)
            else:
                out_dict[device_id] = None

        return out_dict

    def delete_file(self, target, path):
        """Delete a file from a device

        :param target: The device(s) to be targeted with this request
        :type target: :class:`devicecloud.sci.TargetABC` or list of :class:`devicecloud.sci.TargetABC` instances
        :param path: The path on the target to the file to delete.
        :return: A dictionary with keys being device ids and value being None if successful or an :class:`~.ErrorInfo`
            if the operation failed on that device
        :raises: :class:`~.ResponseParseError` If the SCI response has unrecognized formatting
        """
        commands_el = ET.Element('commands')
        rm_el = ET.SubElement(commands_el, 'rm')
        rm_el.set('path', path)
        root = _parse_command_response(self._sci_api.send_sci("file_system", target, ET.tostring(commands_el)))

        out_dict = {}
        for device in root.findall('./file_system/device'):
            device_id = device.get('id')
            error = device.find('.//error')
            if error is not None:
                out_dict[device_id] = _parse_error_tree(error)
            else:
                out_dict[device_id] = None
        return out_dict

    def get_modified_items(self, target, path, last_modified_cutoff):
        """Get all files and directories from a path on the device modified since a given time

        :param target: The device(s) to be targeted with this request
        :type target: :class:`devicecloud.sci.TargetABC` or list of :class:`devicecloud.sci.TargetABC` instances
        :param path: The path on the target to the directory to check for modified files.
        :param last_modified_cutoff: The time (as Unix epoch time) to get files modified since
        :type last_modified_cutoff: int
        :return: A dictionary where the key is a device id and the value is either an :class:`~.ErrorInfo` if there
            was a problem with the operation or a :class:`~.LsInfo` with the items modified since the
            specified date
        """
        file_list = self.list_files(target, path)
        out_dict = {}
        for device_id, device_data in six.iteritems(file_list):
            if isinstance(device_data, ErrorInfo):
                out_dict[device_id] = device_data
            else:
                files = []
                dirs = []
                for cur_file in device_data.files:
                    if cur_file.last_modified > last_modified_cutoff:
                        files.append(cur_file)

                for cur_dir in device_data.directories:
                    if cur_dir.last_modified > last_modified_cutoff:
                        dirs.append(cur_dir)
                out_dict[device_id] = LsInfo(directories=dirs, files=files)

        return out_dict
