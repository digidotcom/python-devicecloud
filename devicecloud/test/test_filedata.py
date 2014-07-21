import base64
import unittest
from xml.etree import ElementTree
import datetime

from devicecloud.test.test_utilities import HttpTestBase


# TODO: get production sample... this was just put together while on plane
GET_FILEDATA_SIMPLE = """\
{
    "items": [
        {
            "fdType": "file",
            "id": { "fdName": "test.txt", "fdPath": "/db/blah/" },
            "fdLastModifiedDate": "2014-07-20T18:46:45.123Z",
            "fdContentType": "application/binary",
            "cstId": "1234",
            "fdCreatedDate": "2014-07-20T18:46:45.123Z",
            "fdSize":  "1234"
        },
        {
            "fdType": "directory",
            "id": { "fdName": "", "fdPath": "/db/blah/" },
            "fdLastModifiedDate": "2014-07-20T18:46:45.123Z",
            "fdContentType": "application/xml",
            "cstId": "1234",
            "fdCreatedDate": "2014-07-20T18:46:45.123Z",
            "fdSize":  "0"
        }
    ]
}
"""


class TestFileData(HttpTestBase):

    def test_get_filedata_simple(self):
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_SIMPLE)
        objects = self.dc.filedata.get_filedata()
        self.assertEqual(len(objects), 2)

    def test_write_file_simple(self):
        self.prepare_response("PUT", "/ws/FileData/test/path/test.txt", "<???>", status=200)
        data = "".join(map(chr, range(255)))
        self.dc.filedata.write_file(
            path="test/path",
            name="test.txt",
            data=data,
            content_type="application/binary",
            archive=True
        )
        req = self._get_last_request()
        root = ElementTree.fromstring(req.body)
        self.assertEqual(root.find("fdContentType").text, "application/binary")
        self.assertEqual(root.find("fdType").text, "file")
        self.assertEqual(base64.decodestring(root.find("fdData").text), data)
        self.assertEqual(root.find("fdArchive").text, "true")

    def test_walk(self):
        self.fail("A test must be added for this")

class TestFileDataObject(HttpTestBase):

    def test_file_metadata_access(self):
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_SIMPLE)
        objects = self.dc.filedata.get_filedata()
        self.assertEqual(len(objects), 2)
        obj = objects[0]
        self.assertEqual(obj.get_path(), "/db/blah/")
        self.assertEqual(obj.get_name(), "test.txt")
        self.assertEqual(obj.get_type(), "file")
        self.assertEqual(obj.get_content_type(), "application/binary")
        self.assertEqual(obj.get_last_modified_date(),
                         datetime.datetime(2014, 7, 20, 18, 46, 45, 123000))
        self.assertEqual(obj.get_created_date(),
                         datetime.datetime(2014, 7, 20, 18, 46, 45, 123000))
        self.assertEqual(obj.get_customer_id(), "1234")
        self.assertEqual(obj.get_full_path(), "/db/blah/test.txt")
        self.assertEqual(obj.get_size(), 1234)

    def test_directory_metadata_access(self):
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_SIMPLE)
        objects = self.dc.filedata.get_filedata()
        self.assertEqual(len(objects), 2)
        obj = objects[1]
        self.assertEqual(obj.get_path(), "/db/blah/")
        self.assertEqual(obj.get_name(), "")
        self.assertEqual(obj.get_type(), "directory")
        self.assertEqual(obj.get_content_type(), "application/xml")
        self.assertEqual(obj.get_last_modified_date(),
                         datetime.datetime(2014, 7, 20, 18, 46, 45, 123000))
        self.assertEqual(obj.get_created_date(),
                         datetime.datetime(2014, 7, 20, 18, 46, 45, 123000))
        self.assertEqual(obj.get_customer_id(), "1234")
        self.assertEqual(obj.get_full_path(), "/db/blah/")
        self.assertEqual(obj.get_size(), 0)


if __name__ == "__main__":
    unittest.main()
