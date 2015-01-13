import base64
import unittest
from xml.etree import ElementTree
import datetime

from dateutil.tz import tzutc
from devicecloud.test.unit.test_utilities import HttpTestBase
import six


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
            "fdSize":  "1234",
            "fdData": "QSBtYW4gYSBwbGFuIGEgY2FuYWwgcGFuYW1h"
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

# Paging Test
GET_FILEDATA_PAGE1 = """\
{
    "resultTotalRows": "2",
    "requestedStartRow": "0",
    "resultSize": "1",
    "requestedSize": "1",
    "remainingSize": "1",
    "items": [
{ "id": { "fdPath": "\/db\/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne\/test_dir\/", "fdName": "test_file.txt"}, "cstId": "304", "fdCreatedDate": "2014-07-13T04:37:16.283Z", "fdLastModifiedDate": "2014-08-07T03:57:09.393Z", "fdContentType": "text\/plain", "fdSize": "149", "fdType": "file", "fdData": "PEZpbGVEYXRhPjxmZENvbnRlbnRUeXBlPnRleHQvcGxhaW48L2ZkQ29udGVudFR5cGU+PGZkVHlwZT5maWxlPC9mZFR5cGU+PGZkRGF0YT5TR1ZzYkd4dkxDQjNiM0pzWkNFPQo8L2ZkRGF0YT48ZmRBcmNoaXZlPmZhbHNlPC9mZEFyY2hpdmU+PC9GaWxlRGF0YT4="}
   ]
 }
"""

GET_FILEDATA_PAGE2 = """\
{
    "resultTotalRows": "2",
    "requestedStartRow": "1",
    "resultSize": "1",
    "requestedSize": "1",
    "remainingSize": "0",
    "items": [
{ "id": { "fdPath": "\/db\/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne\/test_dir\/", "fdName": "test_file2.txt"}, "cstId": "304", "fdCreatedDate": "2014-08-07T03:56:22.013Z", "fdLastModifiedDate": "2014-08-07T03:57:10.057Z", "fdContentType": "text\/plain", "fdSize": "108", "fdType": "file", "fdData": "PEZpbGVEYXRhPjxmZFR5cGU+ZmlsZTwvZmRUeXBlPjxmZERhdGE+U0dWc2JHOHNJR0ZuWVdsdUlRPT0KPC9mZERhdGE+PGZkQXJjaGl2ZT5mYWxzZTwvZmRBcmNoaXZlPjwvRmlsZURhdGE+"}
   ]
 }
"""

# These were grabbed from the live cloud
GET_HOME_RESULT = '{\n    "resultTotalRows": "3",\n    "requestedStartRow": "0",\n    "resultSize": "3",\n    "requestedSize": "1000",\n    "remainingSize": "0",\n    "items": [\n{ "id": { "fdPath": "\\/db\\/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne\\/", "fdName": "00000000-00000000-0004F3FF-FF027D8C"}, "cstId": "304", "fdCreatedDate": "2011-10-13T21:21:58.110Z", "fdLastModifiedDate": "2011-10-13T21:21:58.110Z", "fdContentType": "application\\/xml", "fdSize": "0", "fdType": "directory"},\n{ "id": { "fdPath": "\\/db\\/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne\\/", "fdName": "00000000-00000000-080027FF-FFB1A2C2"}, "cstId": "304", "fdCreatedDate": "2012-01-16T02:22:16.510Z", "fdLastModifiedDate": "2012-01-16T02:22:16.510Z", "fdContentType": "application\\/xml", "fdSize": "0", "fdType": "directory"},\n{ "id": { "fdPath": "\\/db\\/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne\\/", "fdName": "test_dir"}, "cstId": "304", "fdCreatedDate": "2014-07-13T04:37:16.287Z", "fdLastModifiedDate": "2014-07-13T04:37:16.287Z", "fdContentType": "application\\/xml", "fdSize": "0", "fdType": "directory"}\n   ]\n }\n'
GET_DIR1_RESULT = '{\n    "resultTotalRows": "0",\n    "requestedStartRow": "0",\n    "resultSize": "0",\n    "requestedSize": "1000",\n    "remainingSize": "0",\n    "items": [\n    ]\n }\n'
GET_DIR2_RESULT = '{\n    "resultTotalRows": "0",\n    "requestedStartRow": "0",\n    "resultSize": "0",\n    "requestedSize": "1000",\n    "remainingSize": "0",\n    "items": [\n    ]\n }\n'
GET_DIR3_RESULT = '{\n    "resultTotalRows": "1",\n    "requestedStartRow": "0",\n    "resultSize": "1",\n    "requestedSize": "1000",\n    "remainingSize": "0",\n    "items": [\n{ "id": { "fdPath": "\\/db\\/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne\\/test_dir\\/", "fdName": "test_file.txt"}, "cstId": "304", "fdCreatedDate": "2014-07-13T04:37:16.283Z", "fdLastModifiedDate": "2014-07-21T06:14:13.550Z", "fdContentType": "text\\/plain", "fdSize": "149", "fdType": "file"}\n   ]\n }\n'

# This includes embedded data
GET_WITH_EMBED = '{\n    "resultTotalRows": "1",\n    ' \
                 '"requestedStartRow": "0",\n    ' \
                 '"resultSize": "1",\n    ' \
                 '"requestedSize": "1000",\n    ' \
                 '"remainingSize": "0",\n    ' \
                 '"items": ' \
                 '[\n{ ' \
                 '"id": { ' \
                 '"fdPath": "\\/db\\/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne\\/test_dir\\/", ' \
                 '"fdName": "test_file.txt"}, ' \
                 '"cstId": "304", ' \
                 '"fdCreatedDate": "2014-07-13T04:37:16.283Z", ' \
                 '"fdLastModifiedDate": "2014-07-21T07:30:15.383Z", ' \
                 '"fdContentType": "text\\/plain", ' \
                 '"fdSize": "149", ' \
                 '"fdType": "file", ' \
                 '"fdData": "PEZpbGVEYXRhPjxmZENvbnRlbnRUeXBlPnRleHQvcGxhaW48L2ZkQ29udGVudFR5cGU+PGZkVHlwZT5maWxlPC9mZFR5cGU+PGZkRGF0YT5TR1ZzYkd4dkxDQjNiM0pzWkNFPQo8L2ZkRGF0YT48ZmRBcmNoaXZlPmZhbHNlPC9mZEFyY2hpdmU+PC9GaWxlRGF0YT4="}\n   ]\n }\n'


class TestFileData(HttpTestBase):
    def test_get_filedata_simple(self):
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_SIMPLE)
        objects = list(self.dc.filedata.get_filedata())
        self.assertEqual(len(objects), 2)

    def test_get_filedata_paged(self):
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_PAGE1)
        gen = self.dc.filedata.get_filedata(page_size=1)
        obj1 = six.next(gen)
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_PAGE2)
        obj2 = six.next(gen)
        self.assertRaises(StopIteration, six.next, gen)
        self.assertEqual(obj1.get_name(), "test_file.txt")
        self.assertEqual(obj2.get_name(), "test_file2.txt")

    def test_write_file_simple(self):
        self.prepare_response("PUT", "/ws/FileData/test/path/test.txt", "<???>", status=200)
        data = six.b(''.join(map(chr, range(255))))
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
        fd_data = root.find("fdData").text
        self.assertEqual(base64.decodestring(six.b(fd_data)), data)
        self.assertEqual(root.find("fdArchive").text, "true")

    def test_delete_path(self):
        self.prepare_response("DELETE", "/ws/FileData/test", "")
        self.dc.filedata.delete_file("/test")
        req = self._get_last_request()
        self.assertEqual(req.method, "DELETE")
        self.assertEqual(req.path, "/ws/FileData/test")

    def test_walk(self):
        self.prepare_response("GET", "/ws/FileData", GET_HOME_RESULT)
        gen = self.dc.filedata.walk()
        dirpath, dirnames, filenames = six.next(gen)
        self.assertEqual(dirpath, "~/")
        self.assertEqual(len(dirnames), 3)
        self.assertEqual([x.get_full_path() for x in dirnames], [
            '/db/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne/00000000-00000000-0004F3FF-FF027D8C',
            '/db/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne/00000000-00000000-080027FF-FFB1A2C2',
            '/db/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne/test_dir'])
        self.assertEqual(filenames, [])

        # Dir 1
        self.prepare_response("GET", "/ws/FileData", GET_DIR1_RESULT)
        dirpath, dirnames, filenames = six.next(gen)
        self.assertEqual(dirpath,
                         "/db/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne/00000000-00000000-0004F3FF-FF027D8C")
        self.assertEqual(dirnames, [])
        self.assertEqual(filenames, [])

        # Dir 2
        self.prepare_response("GET", "/ws/FileData", GET_DIR2_RESULT)
        dirpath, dirnames, filenames = six.next(gen)
        self.assertEqual(dirpath,
                         "/db/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne/00000000-00000000-080027FF-FFB1A2C2")
        self.assertEqual(dirnames, [])
        self.assertEqual(filenames, [])

        # Dir 3
        self.prepare_response("GET", "/ws/FileData", GET_DIR3_RESULT)
        dirpath, dirnames, filenames = six.next(gen)
        self.assertEqual(dirpath, "/db/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne/test_dir")
        self.assertEqual(dirnames, [])
        self.assertEqual(len(filenames), 1)
        f = filenames[0]
        self.assertEqual(f.get_full_path(),
                         "/db/CUS0000033_Spectrum_Design_Solutions__Paul_Osborne/test_dir/test_file.txt")


class TestFileDataObject(HttpTestBase):

    def test_file_delete(self):
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_SIMPLE)
        objects = list(self.dc.filedata.get_filedata())
        self.assertEqual(len(objects), 2)
        obj = objects[0]
        self.assertEqual(obj.get_full_path(), "/db/blah/test.txt")

        self.prepare_response("DELETE", "/ws/FileData/db/blah/test.txt", "")
        obj.delete()
        req = self._get_last_request()
        self.assertEqual(req.method, "DELETE")
        self.assertEqual(req.path, "/ws/FileData/db/blah/test.txt")

    def test_file_metadata_access(self):
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_SIMPLE)
        objects = list(self.dc.filedata.get_filedata())
        self.assertEqual(len(objects), 2)
        obj = objects[0]
        self.assertEqual(obj.get_path(), "/db/blah/")
        self.assertEqual(obj.get_name(), "test.txt")
        self.assertEqual(obj.get_type(), "file")
        self.assertEqual(obj.get_content_type(), "application/binary")
        self.assertEqual(obj.get_last_modified_date(),
                         datetime.datetime(2014, 7, 20, 18, 46, 45, 123, tzinfo=tzutc()))
        self.assertEqual(obj.get_created_date(),
                         datetime.datetime(2014, 7, 20, 18, 46, 45, 123, tzinfo=tzutc()))
        self.assertEqual(obj.get_customer_id(), "1234")
        self.assertEqual(obj.get_full_path(), "/db/blah/test.txt")
        self.assertEqual(obj.get_size(), 1234)
        self.assertEqual(obj.get_data(), six.b("A man a plan a canal panama"))

    def test_directory_metadata_access(self):
        self.prepare_response("GET", "/ws/FileData", GET_FILEDATA_SIMPLE)
        objects = list(self.dc.filedata.get_filedata())
        self.assertEqual(len(objects), 2)
        obj = objects[1]
        self.assertEqual(obj.get_path(), "/db/blah/")
        self.assertEqual(obj.get_name(), "")
        self.assertEqual(obj.get_type(), "directory")
        self.assertEqual(obj.get_content_type(), "application/xml")
        self.assertEqual(obj.get_last_modified_date(),
                         datetime.datetime(2014, 7, 20, 18, 46, 45, 123, tzinfo=tzutc()))
        self.assertEqual(obj.get_created_date(),
                         datetime.datetime(2014, 7, 20, 18, 46, 45, 123, tzinfo=tzutc()))
        self.assertEqual(obj.get_customer_id(), "1234")
        self.assertEqual(obj.get_full_path(), "/db/blah/")
        self.assertEqual(obj.get_size(), 0)
        self.assertEqual(obj.get_data(), None)


if __name__ == "__main__":
    unittest.main()
