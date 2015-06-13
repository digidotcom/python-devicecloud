# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.

"""Provide access to the device cloud filedata API"""

import base64

from devicecloud.apibase import APIBase
from devicecloud.conditions import Attribute, Expression
from devicecloud.util import iso8601_to_dt, validate_type
import six


fd_path = Attribute("fdPath")
fd_name = Attribute("fdName")
fd_type = Attribute("fdType")
fd_customer_id = Attribute("customer_id")
fd_created_date = Attribute("fdCreatedDate")
fd_last_modified_date = Attribute("fdLastModifiedDate")
fd_content_type = Attribute("fdContentType")
fd_size = Attribute("fdSize")


class FileDataAPI(APIBase):
    """Encapsulate data and logic required to interact with the device cloud file data store"""

    def get_filedata(self, condition=None, page_size=1000):
        """Return a generator over all results matching the provided condition

        :param condition: An :class:`.Expression` which defines the condition
            which must be matched on the filedata that will be retrieved from
            file data store. If a condition is unspecified, the following condition
            will be used ``fd_path == '~/'``.  This condition will match all file
            data in this accounts "home" directory (a sensible root).
        :type condition: :class:`.Expression` or None
        :param int page_size: The number of results to fetch in a single page.  Regardless
            of the size specified, :meth:`.get_filedata` will continue to fetch pages
            and yield results until all items have been fetched.
        :return: Generator yielding :class:`.FileDataObject` instances matching the
            provided conditions.

        """

        condition = validate_type(condition, type(None), Expression, *six.string_types)
        page_size = validate_type(page_size, *six.integer_types)
        if condition is None:
            condition = (fd_path == "~/")  # home directory

        params = {"embed": "true", "condition": condition.compile()}
        for fd_json in self._conn.iter_json_pages("/ws/FileData", page_size=page_size, **params):
            yield FileDataObject.from_json(self, fd_json)

    def write_file(self, path, name, data, content_type=None, archive=False,
                   raw=False):
        """Write a file to the file data store at the given path

        :param str path: The path (directory) into which the file should be written.
        :param str name: The name of the file to be written.
        :param data: The binary data that should be written into the file.
        :type data: str (Python2) or bytes (Python3)
        :param content_type: The content type for the data being written to the file.  May
             be left unspecified.
        :type content_type: str or None
        :param bool archive: If true, history will be retained for various revisions of this
            file.  If this is not required, leave as false.
        :param bool raw: If true, skip the FileData XML headers (necessary for binary files)

        """
        path = validate_type(path, *six.string_types)
        name = validate_type(name, *six.string_types)
        data = validate_type(data, six.binary_type)
        content_type = validate_type(content_type, type(None), *six.string_types)
        archive_str = "true" if validate_type(archive, bool) else "false"

        if not path.startswith("/"):
            path = "/" + path
        if not path.endswith("/"):
            path += "/"
        name = name.lstrip("/")

        sio = six.moves.StringIO()
        if not raw:
            if six.PY3:
                base64_encoded_data = base64.encodebytes(data).decode('utf-8')
            else:
                base64_encoded_data = base64.encodestring(data)

            sio.write("<FileData>")
            if content_type is not None:
                sio.write("<fdContentType>{}</fdContentType>".format(content_type))
            sio.write("<fdType>file</fdType>")
            sio.write("<fdData>{}</fdData>".format(base64_encoded_data))
            sio.write("<fdArchive>{}</fdArchive>".format(archive_str))
            sio.write("</FileData>")
        else:
            sio.write(data)

        params = {
            "type": "file",
            "archive": archive_str
        }
        self._conn.put(
            "/ws/FileData{path}{name}".format(path=path, name=name),
            sio.getvalue(),
            params=params)

    def delete_file(self, path):
        """Delete a file or directory from the filedata store

        This method removes a file or directory (recursively) from
        the filedata store.

        :param path: The path of the file or directory to remove
            from the file data store.

        """
        path = validate_type(path, *six.string_types)
        if not path.startswith("/"):
            path = "/" + path

        self._conn.delete("/ws/FileData{path}".format(path=path))


    def walk(self, root="~/"):
        """Emulation of os.walk behavior against the device cloud filedata store

        This method will yield tuples in the form ``(dirpath, FileDataDirectory's, FileData's)``
        recursively in pre-order (depth first from top down).

        :param str root: The root path from which the search should commence.  By default, this
            is the root directory for this device cloud account (~).
        :return: Generator yielding 3-tuples of dirpath, directories, and files
        :rtype: 3-tuple in form (dirpath, list of :class:`FileDataDirectory`, list of :class:`FileDataFile`)

        """
        root = validate_type(root, *six.string_types)

        directories = []
        files = []

        # fd_path is real picky
        query_fd_path = root
        if not query_fd_path.endswith("/"):
            query_fd_path += "/"

        for fd_object in self.get_filedata(fd_path == query_fd_path):
            if fd_object.get_type() == "directory":
                directories.append(fd_object)
            else:
                files.append(fd_object)

        # Yield the walk results for this level of the tree
        yield (root, directories, files)

        # recurse on each directory and yield results up the chain
        for directory in directories:
            for dirpath, directories, files in self.walk(directory.get_full_path()):
                yield (dirpath, directories, files)


class FileDataObject(object):
    """Encapsulate state and logic surrounding a "filedata" element"""

    @classmethod
    def from_json(cls, fdapi, json_data):
        fd_type = json_data["fdType"]
        if fd_type == "directory":
            return FileDataDirectory.from_json(fdapi, json_data)
        else:
            return FileDataFile.from_json(fdapi, json_data)

    def __init__(self, fdapi, json_data):
        self._fdapi = fdapi
        self._json_data = json_data

    def delete(self):
        """Delete this file or directory"""
        return self._fdapi.delete_file(self.get_full_path())

    def get_data(self):
        """Get the data associated with this filedata object

        :returns: Data associated with this object or None if none exists
        :rtype: str (Python2)/bytes (Python3) or None

        """
        # NOTE: we assume that the "embed" option is used
        base64_data = self._json_data.get("fdData")
        if base64_data is None:
            return None
        else:
            # need to convert to bytes() with python 3
            return base64.decodestring(six.b(base64_data))

    def get_type(self):
        """Get the type (file/directory) of this object"""
        return self._json_data["fdType"]

    def get_last_modified_date(self):
        """Get the last modified datetime of this object"""
        return iso8601_to_dt(self._json_data["fdLastModifiedDate"])

    def get_content_type(self):
        """Get the content type of this object (or None)"""
        return self._json_data["fdContentType"]

    def get_customer_id(self):
        """Get the customer ID associated with this object"""
        return self._json_data["cstId"]

    def get_created_date(self):
        """Get the datetime this object was created"""
        return iso8601_to_dt(self._json_data["fdCreatedDate"])

    def get_name(self):
        """Get the name of this object"""
        return self._json_data["id"]["fdName"]

    def get_path(self):
        """Get the path of this object"""
        return self._json_data["id"]["fdPath"]

    def get_full_path(self):
        """Get the full path (path and name) of this object"""
        return "{}{}".format(self.get_path(), self.get_name())

    def get_size(self):
        """Get this size of this object (will be 0 for directories)"""
        return int(self._json_data["fdSize"])


class FileDataDirectory(FileDataObject):
    """Provide access to a directory and its metadata in the filedata store"""

    @classmethod
    def from_json(cls, fdapi, json_data):
        return cls(fdapi, json_data)

    def __init__(self, fdapi, data):
        FileDataObject.__init__(self, fdapi, data)

    def __repr__(self):
        return "FileDataDirectory({!r})".format(self._json_data)

    def walk(self):
        """Walk the directories and files rooted with this directory

        This method will yield tuples in the form ``(dirpath, FileDataDirectory's, FileData's)``
        recursively in pre-order (depth first from top down).

        :return: Generator yielding 3-tuples of dirpath, directories, and files
        :rtype: 3-tuple in form (dirpath, list of :class:`FileDataDirectory`, list of :class:`FileDataFile`)

        """
        return self._fdapi.walk(root=self.get_path())

    def write_file(self, *args, **kwargs):
        """Write a file into this directory

        This method takes the same arguments as :meth:`.FileDataAPI.write_file`
        with the exception of the ``path`` argument which is not needed here.

        """
        return self._fdapi.write_file(self.get_path(), *args, **kwargs)


class FileDataFile(FileDataObject):
    """Provide access to a file and its metadata in the filedata store"""

    @classmethod
    def from_json(cls, fdapi, json_data):
        return cls(fdapi, json_data)

    def __init__(self, fdapi, json_data):
        FileDataObject.__init__(self, fdapi, json_data)

    def __repr__(self):
        return "FileDataFile({!r})".format(self._json_data)
