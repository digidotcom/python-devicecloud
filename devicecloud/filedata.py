# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

"""Provide access to the device cloud filedata API"""

from xml.etree import ElementTree
import base64
import hashlib
import json

from devicecloud.apibase import APIBase
from devicecloud.conditions import Attribute, Expression
from devicecloud.util import iso8601_to_dt, validate_type
import six


PUT_FILE_TEMPLATE = """
<FileData>
    <fdContentType>text/xml</fdContentType>
    <fdType>file</fdType>
    <fdData>{file_data}</fdData>
    <fdArchive>true</fdArchive>
</FileData>
"""


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
        """Return a generator over all results matching the provided condition"""

        condition = validate_type(condition, type(None), Expression, *six.string_types)
        page_size = validate_type(page_size, *six.integer_types)

        # TODO: implementing paging over the result set
        if condition is None:
            condition = (fd_path == "~/")  # home directory
        response = self._conn.get_json("/ws/FileData?condition={}".format(condition.compile()))

        objects = []
        for fd_json in response.get("items", []):
            objects.append(FileDataObject.from_json(fd_json))
        return objects

    def write_file(self, path, name, data, content_type=None, archive=False):
        path = validate_type(path, *six.string_types)
        name = validate_type(name, *six.string_types)
        data = validate_type(data, *six.string_types)
        content_type = validate_type(content_type, type(None), *six.string_types)
        archive = validate_type(archive, bool)

        if not path.startswith("/"):
            path = "/" + path
        if not path.endswith("/"):
            path += "/"
        name = name.lstrip("/")

        sio = six.StringIO()
        sio.write("<FileData>")
        if content_type is not None:
            sio.write("<fdContentType>{}</fdContentType>".format(content_type))
        sio.write("<fdType>file</fdType>")
        sio.write("<fdData>{}</fdData>".format(base64.encodestring(data)))
        sio.write("<fdArchive>{}</fdArchive>".format("true" if archive else "false"))
        sio.write("</FileData>")

        params = {
            "type": "file",
            "archive": "true" if archive else "false"
        }
        self._conn.put(
            "/ws/FileData{path}{name}".format(path=path,name=name),
            sio.getvalue(),
            params=params)

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
    def from_json(cls, json_data):
        fd_type = json_data["fdType"]
        if fd_type == "directory":
            return FileDataDirectory.from_json(json_data)
        else:
            return FileDataFile.from_json(json_data)

    def __init__(self, json_data):
        self._json_data = json_data

    def get_type(self):
        return self._json_data["fdType"]

    def get_last_modified_date(self):
        return iso8601_to_dt(self._json_data["fdLastModifiedDate"])

    def get_content_type(self):
        return self._json_data["fdContentType"]

    def get_customer_id(self):
        return self._json_data["cstId"]

    def get_created_date(self):
        return iso8601_to_dt(self._json_data["fdCreatedDate"])

    def get_name(self):
        return self._json_data["id"]["fdName"]

    def get_path(self):
        return self._json_data["id"]["fdPath"]

    def get_full_path(self):
        return "{}{}".format(self.get_path(), self.get_name())

    def get_size(self):
        return self._json_data["fdSize"]


class FileDataDirectory(FileDataObject):

    @classmethod
    def from_json(cls, json_data):
        return cls(json_data)

    def __init__(self, data):
        FileDataObject.__init__(self, data)

    def __repr__(self):
        return "FileDataDirectory({!r})".format(self._json_data)


class FileDataFile(FileDataObject):

    @classmethod
    def from_json(cls, json_data):
        return cls(json_data)

    def __init__(self, json_data):
        FileDataObject.__init__(self, json_data)

    def __repr__(self):
        return "FileDataFile({!r})".format(self._json_data)
