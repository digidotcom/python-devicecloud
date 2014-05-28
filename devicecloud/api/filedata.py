from apibase import APIBase
from xml.etree import ElementTree
import base64
import hashlib
import json
from devicecloud.util import iso8601_to_dt

PUT_FILE_TEMPLATE = """
<FileData>
    <fdContentType>text/xml</fdContentType>
    <fdType>file</fdType>
    <fdData>{file_data}</fdData>
    <fdArchive>true</fdArchive>
</FileData>
"""


class FileDataAPI(APIBase):
    def get_files(self, file_glob, device, from_date, contents):
        condition = ["fdName like '%s'" % file_glob, ]
        if device is not None:
            condition.append("fdPath like '%%/%s/%%'" % device.connectware_id)
        if from_date is not None:
            condition.append("fdLastModifiedDate>'%s'" % from_date)
        if len(condition) > 1:
            condition = ' and '.join(condition)
        filedata_response = self._conn.get("/ws/FileData",
                                           params={'condition': condition,
                                                   'embed': contents})
        root = ElementTree.fromstring(filedata_response)
        files = []
        for el in root.findall(".//FileData"):
            files.append(FileData.from_filedata(el))
        return files

    def put_file(self, file_name, file_data):
        path = "/ws/FileData/~/%s" % file_name
        data = PUT_FILE_TEMPLATE.format(file_data=base64.encodestring(file_data))
        response = self._conn.put(path, data)
        return response


class FileData(object):
    @classmethod
    def from_filedata(cls, el):
        """Create a FileData object from FileData etree data"""
        fd_path = el.find(".//fdPath").text
        fd_name = el.find(".//fdName").text
        fd_last_modified = el.find(".//fdLastModifiedDate").text
        fd_content_type = el.find(".//fdContentType").text
        fd_size = el.find('.//fdSize').text
        el_data = el.find('.//fdData')
        if el_data is not None:
            fd_data = base64.decodestring(el_data.text)
        else:
            fd_data = ""
        return cls(fd_path, fd_name, fd_last_modified,
                   fd_content_type, fd_data, fd_size)

    def __init__(self, fd_path, fd_name, fd_last_modified,
                 fd_content_type, fd_data, fd_size):
        self.path = fd_path
        self.name = fd_name
        self.last_modified = fd_last_modified
        self.content_type = fd_content_type
        self.data = fd_data
        self.size = fd_size
        self.checksum = hashlib.md5(self.data).hexdigest()

    def __str__(self):
        return "FileData(%s - %s)" % (self.get_last_modified(dt=True), self.name)

    def decode_data(self):
        if self.content_type == "application/json":
            return json.loads(self.data)
        return self.data

    def get_last_modified(self, dt=False):
        """Return dt string, use dt=True to return datetime obj"""
        if dt:
            return iso8601_to_dt(self.last_modified)
        else:
            return self.last_modified
