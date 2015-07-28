import base64
import unittest
from xml.etree import ElementTree as ET

from devicecloud.file_system_service import FileInfo, DirectoryInfo, FileSystemServiceException, \
    _parse_command_response, ResponseParseError, \
    ErrorInfo, LsInfo, _parse_error_tree, LsCommand, GetCommand, PutCommand, DeleteCommand, \
    FileSystemServiceCommandBlock
from devicecloud.sci import AllTarget
from devicecloud.test.unit.test_utilities import HttpTestBase
import mock
import six


class FileSystemResponse(object):
    def __init__(self):
        self.string_start = "<sci_reply version=\"1.0\"><file_system>"
        self.end_string = "</file_system></sci_reply>"
        self.block = ""

    def add_device_block(self, dev_id, command_block):
        block = "<device id=\"{dev_id}\"><commands>{command_block}</commands></device>"
        self.block += block.format(dev_id=dev_id, command_block=command_block)

    def get_string(self):
        return self.string_start + self.block + self.end_string

    @property
    def text(self):
        return self.string_start + self.block + self.end_string


LS_BLOCK = """\
<ls hash="md5">
<dir path="/a/path/dir" last_modified="1436203917"/>
<file path="/a/path/file1.txt" last_modified="1436276773" size="7989" hash="967FDA522517B9CE0C3E056EDEB485BB"/>
<file path="/a/path/file2.py" last_modified="1434377919" size="181" hash="DEA17715739E46079C1A6DDCB38344DF"/>
</ls>
"""

ERROR_BLOCK = """\
<{command}>
<error id="{errno}">{errtext}</error>
</{command}>
"""

GET_FILE_BLOCK = """\
<get_file>
<data>{data}</data>
</get_file>
"""

GENERIC_COMMAND_BLOCK = """<{command}></{command}>"""

PUT_FILE_DATA_COMMAND = """\
<commands>\
<put_file {offset}path="{path}" truncate="{truncate}">\
<data>{data}</data>\
</put_file>\
</commands>\
"""

PUT_FILE_FILE_COMMAND = """\
<commands>\
<put_file {offset}path="{path}" truncate="{truncate}">\
<file>{server_file}</file>\
</put_file>\
</commands>\
"""

DELETE_FILE_COMMAND = """\
<commands>\
<rm path="{path}" />\
</commands>\
"""


class TestFileInfo(unittest.TestCase):
    def setUp(self):
        self.fss_api = mock.Mock()
        self.dev_id = '00000000-00000000-18A905FF-FF2F1BBD'

    def test_eq_not_eq(self):
        file1 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        file2 = FileInfo(self.fss_api, self.dev_id, '/a/path/file2.py', 1434377919, 181,
                         "DEA17715739E46079C1A6DDCB38344DF", 'md5')
        self.assertNotEqual(file1, file2)

    def test_eq(self):
        file1 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        file2 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        self.assertEqual(file1, file2)
        self.assertFalse(file1 is file2)

    def test_get_data(self):
        self.fss_api.get_file.side_effect = ({self.dev_id: "some file data"},)
        file1 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        self.assertEqual("some file data", file1.get_data())
        self.assertEqual(1, self.fss_api.get_file.call_count)
        call_name, call_args, call_kwargs = self.fss_api.get_file.mock_calls[0]
        self.assertEqual(call_args[0]._device_id, self.dev_id)
        self.assertEqual(call_args[1], '/a/path/file1.txt')

    def test_get_data_error(self):
        error = ErrorInfo(1, "error message")
        self.fss_api.get_file.side_effect = ({self.dev_id: error},)
        file1 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        self.assertEqual(error, file1.get_data())
        self.assertEqual(1, self.fss_api.get_file.call_count)
        call_name, call_args, call_kwargs = self.fss_api.get_file.mock_calls[0]
        self.assertEqual(call_args[0]._device_id, self.dev_id)
        self.assertEqual(call_args[1], '/a/path/file1.txt')

    def test_delete(self):
        self.fss_api.delete_file.side_effect = ({self.dev_id: None},)
        file1 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        self.assertIsNone(file1.delete())
        self.assertEqual(1, self.fss_api.delete_file.call_count)
        call_name, call_args, call_kwargs = self.fss_api.delete_file.mock_calls[0]
        self.assertEqual(call_args[0]._device_id, self.dev_id)
        self.assertEqual(call_args[1], '/a/path/file1.txt')

    def test_delete_error(self):
        error = ErrorInfo(1, "error message")
        self.fss_api.delete_file.side_effect = ({self.dev_id: error},)
        file1 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        ret_err = file1.delete()
        self.assertEqual(error.errno, ret_err.errno)
        self.assertEqual(error.message, ret_err.message)
        self.assertEqual(1, self.fss_api.delete_file.call_count)
        call_name, call_args, call_kwargs = self.fss_api.delete_file.mock_calls[0]
        self.assertEqual(call_args[0]._device_id, self.dev_id)
        self.assertEqual(call_args[1], '/a/path/file1.txt')


class TestDirectoryInfo(unittest.TestCase):
    def setUp(self):
        self.fss_api = mock.Mock()
        self.dev_id = '00000000-00000000-18A905FF-FF2F1BBD'

    def test_eq_not_eq(self):
        dir1 = DirectoryInfo(self.fss_api, self.dev_id, '/a/path/dir1', 1436276773)
        dir2 = DirectoryInfo(self.fss_api, self.dev_id, '/a/path/dir2', 1434377919)
        self.assertNotEqual(dir1, dir2)

    def test_eq(self):
        dir1 = DirectoryInfo(self.fss_api, self.dev_id, '/a/path/dir1', 1436276773)
        dir2 = DirectoryInfo(self.fss_api, self.dev_id, '/a/path/dir1', 1436276773)
        self.assertEqual(dir1, dir2)
        self.assertFalse(dir1 is dir2)

    def test_list_contents(self):
        file1 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        file2 = FileInfo(self.fss_api, self.dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        self.fss_api.list_files.side_effect = ({self.dev_id: LsInfo([], [file1, file2])},)
        dir1 = DirectoryInfo(self.fss_api, self.dev_id, '/a/path/dir1', 1436276773)
        dirs, files = dir1.list_contents()
        self.assertEqual(0, len(dirs))
        self.assertListEqual([file1, file2], files)
        self.assertEqual(1, self.fss_api.list_files.call_count)
        call_name, call_args, call_kwargs = self.fss_api.list_files.mock_calls[0]
        self.assertEqual(call_args[0]._device_id, self.dev_id)
        self.assertEqual(call_args[1], '/a/path/dir1')


class TestLsCommand(unittest.TestCase):
    def test_init(self):
        lscommand = LsCommand(path='/a/path/here')
        et = lscommand.get_etree()
        self.assertEqual(et.tag, 'ls')
        self.assertEqual('/a/path/here', et.get('path'))
        self.assertEqual('any', et.get('hash'))
        self.assertEqual(0, len(list(et)))
        self.assertEqual(None, et.text)

    def test_parse(self):
        fss_api = mock.Mock()
        dev_id = 'my_dev_id'
        file1 = FileInfo(fss_api, dev_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        file2 = FileInfo(fss_api, dev_id, '/a/path/file2.py', 1434377919, 181,
                         "DEA17715739E46079C1A6DDCB38344DF", 'md5')
        dir1 = DirectoryInfo(fss_api, dev_id, '/a/path/dir', 1436203917)
        linfo = LsCommand.parse_response(ET.fromstring(LS_BLOCK), device_id=dev_id, fssapi=fss_api)
        self.assertEqual(linfo, LsInfo(directories=[dir1], files=[file1, file2]))

    def test_parse_error(self):
        fss_api = mock.Mock()
        dev_id = 'my_dev_id'
        errinfo = LsCommand.parse_response(
            ET.fromstring(ERROR_BLOCK.format(command='ls', errno=1, errtext="error text")),
            device_id=dev_id, fssapi=fss_api)

        self.assertEqual(errinfo.errno, 1)
        self.assertEqual(errinfo.message, "error text")

    def test_parse_wrong_response(self):
        self.assertRaises(ResponseParseError, LsCommand.parse_response, ET.fromstring('<rm />'))


class TestGetCommand(unittest.TestCase):
    def test_init_defaults(self):
        getcommand = GetCommand(path='/a/path/here')
        et = getcommand.get_etree()
        self.assertEqual(et.tag, 'get_file')
        self.assertEqual('/a/path/here', et.get('path'))
        self.assertEqual(None, et.get('offset', None))
        self.assertEqual(None, et.get('length', None))
        self.assertEqual(0, len(list(et)))
        self.assertEqual(None, et.text)

    def test_init_values(self):
        getcommand = GetCommand(path='/a/path/here', offset=5, length=10)
        et = getcommand.get_etree()
        self.assertEqual(et.tag, 'get_file')
        self.assertEqual('/a/path/here', et.get('path'))
        self.assertEqual('5', et.get('offset', None))
        self.assertEqual('10', et.get('length', None))
        self.assertEqual(0, len(list(et)))
        self.assertEqual(None, et.text)

    def test_parse(self):
        data_str = base64.b64encode(six.b("File Data")).decode('ascii')
        data = GetCommand.parse_response(ET.fromstring(GET_FILE_BLOCK.format(data=data_str)))
        self.assertEqual(six.b("File Data"), data)

    def test_parse_error(self):
        errinfo = GetCommand.parse_response(
            ET.fromstring(ERROR_BLOCK.format(command='get_file', errno=1, errtext="error text")))

        self.assertEqual(errinfo.errno, 1)
        self.assertEqual(errinfo.message, "error text")

    def test_parse_wrong_response(self):
        self.assertRaises(ResponseParseError, GetCommand.parse_response, ET.fromstring('<rm />'))


class TestPutCommand(unittest.TestCase):
    def test_init_defaults(self):
        putcommand = PutCommand(path='/a/path/here', file_data=six.b("some file data"))
        et = putcommand.get_etree()
        self.assertEqual(et.tag, 'put_file')
        self.assertEqual('/a/path/here', et.get('path'))
        self.assertEqual(None, et.get('offset', None))
        self.assertEqual('false', et.get('truncate'))
        self.assertEqual(1, len(list(et)))
        data = et.find('./data')
        self.assertEqual(base64.b64encode(six.b("some file data")), six.b(data.text))

    def test_init_server_file(self):
        putcommand = PutCommand(path='/a/path/here', server_file='/a/file/on/server')
        et = putcommand.get_etree()
        self.assertEqual(et.tag, 'put_file')
        self.assertEqual('/a/path/here', et.get('path'))
        self.assertEqual(None, et.get('offset', None))
        self.assertEqual('false', et.get('truncate'))
        self.assertEqual(1, len(list(et)))
        server_file = et.find('./file')
        self.assertEqual('/a/file/on/server', server_file.text)

    def test_init_values(self):
        putcommand = PutCommand(path='/a/path/here', file_data=six.b("some file data"), offset=5, truncate=True)
        et = putcommand.get_etree()
        self.assertEqual(et.tag, 'put_file')
        self.assertEqual('/a/path/here', et.get('path'))
        self.assertEqual('5', et.get('offset', None))
        self.assertEqual('true', et.get('truncate'))
        self.assertEqual(1, len(list(et)))
        data = et.find('./data')
        self.assertEqual(base64.b64encode(six.b("some file data")), six.b(data.text))

    def test_put_command_no_data(self):
        self.assertRaises(FileSystemServiceException, PutCommand, path='/a/path/here')

    def test_put_command_both_data(self):
        self.assertRaises(FileSystemServiceException, PutCommand, path='/a/path/here',
                          file_data=six.b("some file data"),  server_file='/a/file/on/server')

    def test_parse(self):
        self.assertIsNone(PutCommand.parse_response(ET.fromstring('<put_file />')))

    def test_parse_error(self):
        errinfo = PutCommand.parse_response(
            ET.fromstring(ERROR_BLOCK.format(command='put_file', errno=1, errtext="error text")))

        self.assertEqual(errinfo.errno, 1)
        self.assertEqual(errinfo.message, "error text")

    def test_parse_wrong_response(self):
        self.assertRaises(ResponseParseError, PutCommand.parse_response, ET.fromstring('<rm />'))


class TestDeleteCommand(unittest.TestCase):
    def test_init(self):
        delcommand = DeleteCommand(path='/a/path/here')
        et = delcommand.get_etree()
        self.assertEqual(et.tag, 'rm')
        self.assertEqual('/a/path/here', et.get('path'))
        self.assertEqual(0, len(list(et)))
        self.assertEqual(None, et.text)

    def test_parse(self):
        self.assertIsNone(DeleteCommand.parse_response(ET.fromstring('<rm />')))

    def test_parse_error(self):
        errinfo = DeleteCommand.parse_response(
            ET.fromstring(ERROR_BLOCK.format(command='rm', errno=1, errtext="error text")))

        self.assertEqual(errinfo.errno, 1)
        self.assertEqual(errinfo.message, "error text")

    def test_parse_wrong_response(self):
        self.assertRaises(ResponseParseError, DeleteCommand.parse_response, ET.fromstring('<put_file />'))


class TestCommandBlock(unittest.TestCase):
    def test_init(self):
        command_block = FileSystemServiceCommandBlock()
        et = command_block.get_etree()
        self.assertEqual(et.tag, 'commands')
        self.assertEqual(0, len(list(et)))
        self.assertEqual(0, len(et.keys()))

    def test_add_command(self):
        command_block = FileSystemServiceCommandBlock()
        command_block.add_command(DeleteCommand(path='/a/path'))
        et = command_block.get_etree()
        self.assertEqual(et.tag, 'commands')
        self.assertEqual(1, len(list(et)))
        self.assertEqual(0, len(et.keys()))
        self.assertIsNotNone(et.find('./{}'.format(DeleteCommand.command_name)))

    def test_get_command_string(self):
        command_block = FileSystemServiceCommandBlock()
        self.assertEqual(six.b('<commands />'), command_block.get_command_string())
        command_block.add_command(DeleteCommand(path='/a/path'))
        self.assertEqual(six.b('<commands><rm path="/a/path" /></commands>'), command_block.get_command_string())


class TestFileSystemServiceAPI(HttpTestBase):
    def setUp(self):
        HttpTestBase.setUp(self)
        self.fss_api = self.dc.get_fss_api()
        self.sci_api = mock.Mock()
        self.fss_api._sci_api = self.sci_api
        self.target = AllTarget()
        self.dev1_id = '00000000-00000000-18A905FF-FF2F1BBD'
        self.dev2_id = '00000000-00000000-18A905FF-FF2F1BBE'

        # Create some file, directory, and error info objects to use in tests
        self.file1 = FileInfo(self.fss_api, self.dev1_id, '/a/path/file1.txt', 1436276773, 7989,
                         "967FDA522517B9CE0C3E056EDEB485BB", 'md5')
        self.file2 = FileInfo(self.fss_api, self.dev1_id, '/a/path/file2.py', 1434377919, 181,
                         "DEA17715739E46079C1A6DDCB38344DF", 'md5')
        self.dir1 = DirectoryInfo(self.fss_api, self.dev1_id, '/a/path/dir', 1436203917)
        self.errinfo = ErrorInfo(errno=1, message="an error message")

    def clone_file(self, orig_file):
        return FileInfo(orig_file._fssapi, orig_file.device_id, orig_file.path,
                        orig_file.last_modified, orig_file.size, orig_file.hash, orig_file.hash_type)

    def clone_dir(self, orig_dir):
        return DirectoryInfo(orig_dir._fssapi, orig_dir.device_id, orig_dir.path, orig_dir.last_modified)

    def prep_sci_response(self, response):
        self.sci_api.send_sci.side_effect = (response,)

    def test_parse_command_response_bad_xml_response(self):
        fsr = FileSystemResponse()
        fsr.add_device_block('asdf', '<> <asdf>some_garbage_data')
        self.assertRaises(ResponseParseError, _parse_command_response, fsr)

    def test_parse_command_response_good_data(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, "<some_command></some_command>")
        root = _parse_command_response(fsr)
        self.assertIsNotNone(root.find('.//some_command'))

    def test_parse_error_tree_text(self):
        command = ET.fromstring(ERROR_BLOCK.format(command='command', errno=1, errtext="some text"))
        error = command.find('./error')
        errinfo = _parse_error_tree(error)
        self.assertEqual(errinfo.errno, 1)
        self.assertEqual(errinfo.message, 'some text')

    def test_parse_error_tree_desc_node(self):
        command = ET.fromstring(ERROR_BLOCK.format(command='command', errno=1, errtext="<desc>some text</desc>"))
        error = command.find('./error')
        errinfo = _parse_error_tree(error)
        self.assertEqual(errinfo.errno, 1)
        self.assertEqual(errinfo.message, 'some text')

    def test_list_dir(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, LS_BLOCK)
        fsr.add_device_block(self.dev2_id, LS_BLOCK)
        self.prep_sci_response(fsr)
        list_dict = self.fss_api.list_files(self.target, '/a/path/')

        files_dev1 = [self.file1, self.file2]
        dirs_dev1 = [self.dir1]

        file1 = self.clone_file(self.file1)
        file1.device_id = self.dev2_id
        file2 = self.clone_file(self.file2)
        file2.device_id = self.dev2_id

        files_dev2 = [file1, file2]
        dir1 = self.clone_dir(self.dir1)
        dir1.device_id = self.dev2_id
        dirs_dev2 = [dir1]

        expected_dict = {self.dev1_id: LsInfo(dirs_dev1, files_dev1),
                         self.dev2_id: LsInfo(dirs_dev2, files_dev2)}

        self.assertDictEqual(expected_dict, list_dict)

    def test_list_nonexistent_dir(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id,
                             ERROR_BLOCK.format(command="ls", errno=1, errtext="No such file or directory"))
        self.prep_sci_response(fsr)
        out_dict = self.fss_api.list_files(self.target, '/a/nonexistent/path')
        self.assertEqual(1, len(out_dict.keys()))
        self.assertTrue(self.dev1_id in out_dict.keys())
        error = out_dict[self.dev1_id]
        self.assertEqual(1, error.errno)
        self.assertEqual("No such file or directory", error.message)

    def test_get_entire_file(self):
        data_string = base64.b64encode(six.b('testing string')).decode('ascii')
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GET_FILE_BLOCK.format(data=data_string))
        fsr.add_device_block(self.dev2_id, GET_FILE_BLOCK.format(data=data_string))
        self.prep_sci_response(fsr)
        get_file_data = self.fss_api.get_file(self.target, '/a/path/file1.txt')
        expected_dict = {
            self.dev1_id: six.b('testing string'),
            self.dev2_id: six.b('testing string'),
        }
        self.assertDictEqual(expected_dict, get_file_data)

    def test_get_partial_file(self):
        data_string = base64.b64encode(six.b('ting')).decode('ascii')
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GET_FILE_BLOCK.format(data=data_string))
        fsr.add_device_block(self.dev2_id, GET_FILE_BLOCK.format(data=data_string))
        self.prep_sci_response(fsr)
        get_file_data = self.fss_api.get_file(self.target, '/a/path/file1.txt', offset=2, length=4)
        expected_dict = {
            self.dev1_id: six.b('ting'),
            self.dev2_id: six.b('ting'),
        }
        self.assertDictEqual(expected_dict, get_file_data)

    def test_get_nonexistent_file(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id,
                             ERROR_BLOCK.format(command='get_file', errno=1, errtext="No such file or directory"))
        self.prep_sci_response(fsr)
        out_dict = self.fss_api.get_file(self.target, '/a/nonexistent/path')
        self.assertEqual(1, len(out_dict.keys()))
        self.assertTrue(self.dev1_id in out_dict.keys())
        error = out_dict[self.dev1_id]
        self.assertEqual(1, error.errno)
        self.assertEqual("No such file or directory", error.message)

    def test_get_file_some_error(self):
        data_string = base64.b64encode(six.b('testing string')).decode('ascii')
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id,
                             ERROR_BLOCK.format(command='get_file', errno=1, errtext="No such file or directory"))
        fsr.add_device_block(self.dev2_id, GET_FILE_BLOCK.format(data=data_string))
        self.prep_sci_response(fsr)
        out_dict = self.fss_api.get_file(self.target, '/a/nonexistent/path')
        self.assertEqual(2, len(out_dict.keys()))
        self.assertTrue(self.dev1_id in out_dict.keys())
        self.assertTrue(self.dev2_id in out_dict.keys())

        # Verify error info
        error = out_dict[self.dev1_id]
        self.assertEqual(1, error.errno)
        self.assertEqual("No such file or directory", error.message)

        # Verify OK data
        self.assertEqual(six.b('testing string'), out_dict[self.dev2_id])

    def test_put_complete_file(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        fsr.add_device_block(self.dev2_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        out_dict = self.fss_api.put_file(self.target, file_path, file_data=six.b('testing string'))

        expected_dict = {
            self.dev1_id: None,
            self.dev2_id: None
        }
        self.assertDictEqual(expected_dict, out_dict)

        self.sci_api.send_sci.assert_called_once_with('file_system', self.target, six.b(PUT_FILE_DATA_COMMAND.format(
            path=file_path,
            data=base64.b64encode(six.b('testing string')).decode('ascii'),
            offset="",
            truncate='false')))

    def test_put_partial_file(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        fsr.add_device_block(self.dev2_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        out_dict = self.fss_api.put_file(self.target, file_path, file_data=six.b('testing string'), offset=5)
        expected_dict = {
            self.dev1_id: None,
            self.dev2_id: None
        }
        self.assertDictEqual(expected_dict, out_dict)

        self.sci_api.send_sci.assert_called_once_with('file_system', self.target, six.b(PUT_FILE_DATA_COMMAND.format(
            path=file_path,
            data=base64.b64encode(six.b('testing string')).decode('ascii'),
            offset="offset=\"5\" ",
            truncate='false')))

    def test_put_partial_file_truncate(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        fsr.add_device_block(self.dev2_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        out_dict = self.fss_api.put_file(self.target, file_path, file_data=six.b('testing string'), offset=5,
                                         truncate=True)
        expected_dict = {
            self.dev1_id: None,
            self.dev2_id: None
        }
        self.assertDictEqual(expected_dict, out_dict)

        self.sci_api.send_sci.assert_called_once_with('file_system', self.target, six.b(PUT_FILE_DATA_COMMAND.format(
            path=file_path,
            data=base64.b64encode(six.b('testing string')).decode('ascii'),
            offset="offset=\"5\" ",
            truncate='true')))

    def test_put_file_both_data_args(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        fsr.add_device_block(self.dev2_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        self.assertRaises(FileSystemServiceException, self.fss_api.put_file, self.target, file_path,
                          file_data=six.b('testing string'), server_file='/a/path/file2.txt')

    def test_put_file_both_neither_args(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        fsr.add_device_block(self.dev2_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        self.assertRaises(FileSystemServiceException, self.fss_api.put_file, self.target, file_path)

    def test_put_file_server_file(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        fsr.add_device_block(self.dev2_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        server_file = '/a/path/file2.txt'
        out_dict = self.fss_api.put_file(self.target, file_path, server_file=server_file)
        expected_dict = {
            self.dev1_id: None,
            self.dev2_id: None
        }
        self.assertDictEqual(expected_dict, out_dict)

        self.sci_api.send_sci.assert_called_once_with('file_system', self.target, six.b(PUT_FILE_FILE_COMMAND.format(
            path=file_path,
            server_file=server_file,
            offset="",
            truncate='false')))

    def test_put_file_some_error(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='put_file'))
        fsr.add_device_block(self.dev2_id,
                             ERROR_BLOCK.format(command='put_file', errno='1', errtext='something went wrong'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        server_file = '/a/path/file2.txt'
        out_dict = self.fss_api.put_file(self.target, file_path, server_file=server_file)
        self.assertIsNone(out_dict[self.dev1_id])
        error = out_dict[self.dev2_id]
        self.assertEqual(1, error.errno)
        self.assertEqual('something went wrong', error.message)

    def test_delete_file(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='rm'))
        fsr.add_device_block(self.dev2_id, GENERIC_COMMAND_BLOCK.format(command='rm'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        out_dict = self.fss_api.delete_file(self.target, file_path)
        expected_dict = {
            self.dev1_id: None,
            self.dev2_id: None
        }
        self.assertDictEqual(expected_dict, out_dict)

        self.sci_api.send_sci.assert_called_once_with('file_system', self.target, six.b(DELETE_FILE_COMMAND.format(
            path=file_path)))

    def test_delete_file_some_error(self):
        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, GENERIC_COMMAND_BLOCK.format(command='rm'))
        fsr.add_device_block(self.dev2_id, ERROR_BLOCK.format(command='rm', errno='1', errtext='something went wrong'))
        self.prep_sci_response(fsr)
        file_path = '/a/path/file1.txt'
        out_dict = self.fss_api.delete_file(self.target, file_path)
        self.assertIsNone(out_dict[self.dev1_id])
        error = out_dict[self.dev2_id]
        self.assertEqual(1, error.errno)
        self.assertEqual('something went wrong', error.message)

    def test_get_modified_items(self):

        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[], files=[self.file1, self.file2])
            out_dict = {self.dev1_id: linfo, self.dev2_id: LsInfo(directories=[], files=[])}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.get_modified_items(self.target, '/a/path/', self.file1.last_modified - 1)

            expected_out_dict = {
                self.dev1_id: LsInfo(files=[self.file1], directories=[]),
                self.dev2_id: LsInfo([], [])
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_get_modified_items_errinfo(self):
        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[], files=[self.file1, self.file2])
            out_dict = {self.dev1_id: linfo, self.dev2_id: self.errinfo}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.get_modified_items(self.target, '/a/path/', self.file1.last_modified - 1)

            expected_out_dict = {
                self.dev1_id: LsInfo(files=[self.file1], directories=[]),
                self.dev2_id: self.errinfo
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_get_modified_items_no_results(self):
        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[], files=[self.file1, self.file2])
            out_dict = {self.dev1_id: linfo, self.dev2_id: linfo}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.get_modified_items(self.target, '/a/path/', self.file1.last_modified + self.file2.last_modified)

            expected_out_dict = {
                self.dev1_id: LsInfo([], []),
                self.dev2_id: LsInfo([], [])
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_get_modified_items_mult_dev_results(self):
        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[], files=[self.file1, self.file2])
            out_dict = {self.dev1_id: linfo, self.dev2_id: linfo}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.get_modified_items(self.target, '/a/path/', self.file1.last_modified - 1)

            expected_out_dict = {
                self.dev1_id: LsInfo(files=[self.file1], directories=[]),
                self.dev2_id: LsInfo(files=[self.file1], directories=[])
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_get_modified_directory_results(self):
        dir2 = DirectoryInfo(self.fss_api, self.dev1_id, '/a/path/dir2', self.dir1.last_modified - 2)

        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[self.dir1, dir2], files=[])
            out_dict = {self.dev1_id: linfo, self.dev2_id: LsInfo([], [])}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.get_modified_items(self.target, '/a/path/', self.dir1.last_modified - 1)

            expected_out_dict = {
                self.dev1_id: LsInfo(files=[], directories=[self.dir1]),
                self.dev2_id: LsInfo([], [])
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_exists_file(self):
        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[], files=[self.file1])
            out_dict = {self.dev1_id: linfo, self.dev2_id: LsInfo([], [])}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.exists(self.target, self.file1.path)

            expected_out_dict = {
                self.dev1_id: True,
                self.dev2_id: False
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_exists_dir(self):

        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[self.dir1], files=[])
            out_dict = {self.dev1_id: linfo, self.dev2_id: LsInfo([], [])}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.exists(self.target, self.dir1.path)

            expected_out_dict = {
                self.dev1_id: True,
                self.dev2_id: False
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_exists_dir_trailing_slash(self):
        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[self.dir1], files=[])
            out_dict = {self.dev1_id: linfo, self.dev2_id: LsInfo([], [])}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.exists(self.target, self.dir1.path + '/')

            expected_out_dict = {
                self.dev1_id: True,
                self.dev2_id: False
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_exists_errinfo(self):

        def mock_list_files(*args, **kwargs):
            linfo = LsInfo(directories=[], files=[self.file1])
            out_dict = {self.dev1_id: linfo, self.dev2_id: self.errinfo}
            return out_dict

        with mock.patch.object(self.fss_api, 'list_files', side_effect=mock_list_files) as m:
            out_dict = self.fss_api.exists(self.target, self.file1.path)

            expected_out_dict = {
                self.dev1_id: True,
                self.dev2_id: self.errinfo
            }

            self.assertDictEqual(expected_out_dict, out_dict)

    def test_send_command_block_all_ok(self):
        command_block = FileSystemServiceCommandBlock()
        command_block.add_command(DeleteCommand(path='/a/path/1.txt'))
        command_block.add_command(DeleteCommand(path='/a/path/2.txt'))

        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, (GENERIC_COMMAND_BLOCK.format(command='rm') + GENERIC_COMMAND_BLOCK.format(command='rm')))
        fsr.add_device_block(self.dev2_id, (GENERIC_COMMAND_BLOCK.format(command='rm') + GENERIC_COMMAND_BLOCK.format(command='rm')))
        self.prep_sci_response(fsr)

        out_dict = self.fss_api.send_command_block(self.target, command_block)

        # Should just be Nones because they are delete commands with no errors
        expected_dict = {
            self.dev1_id: [None, None],
            self.dev2_id: [None, None],
        }

        self.assertDictEqual(expected_dict, out_dict)

    def test_send_command_block_mixed_commands(self):
        command_block = FileSystemServiceCommandBlock()
        command_block.add_command(DeleteCommand(path='/a/path/1.txt'))
        command_block.add_command(GetCommand(path='/a/path/2.txt'))

        data_string = base64.b64encode(six.b('testing string')).decode('ascii')

        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, (GENERIC_COMMAND_BLOCK.format(command='rm') + GET_FILE_BLOCK.format(data=data_string)))
        fsr.add_device_block(self.dev2_id, (GENERIC_COMMAND_BLOCK.format(command='rm') + GET_FILE_BLOCK.format(data=data_string)))
        self.prep_sci_response(fsr)

        out_dict = self.fss_api.send_command_block(self.target, command_block)

        expected_dict = {
            self.dev1_id: [None, six.b('testing string')],
            self.dev2_id: [None, six.b('testing string')],
        }

        self.assertDictEqual(expected_dict, out_dict)

    def test_send_command_block_errors(self):
        command_block = FileSystemServiceCommandBlock()
        command_block.add_command(DeleteCommand(path='/a/path/1.txt'))
        command_block.add_command(GetCommand(path='/a/path/2.txt'))

        fsr = FileSystemResponse()
        fsr.add_device_block(self.dev1_id, (GENERIC_COMMAND_BLOCK.format(command='rm') + ERROR_BLOCK.format(command='get_file', errno=1, errtext="an error message")))
        fsr.add_device_block(self.dev2_id, (GENERIC_COMMAND_BLOCK.format(command='rm') + ERROR_BLOCK.format(command='get_file', errno=1, errtext="an error message")))
        self.prep_sci_response(fsr)

        out_dict = self.fss_api.send_command_block(self.target, command_block)

        # Check empty DeleteCommand responses
        self.assertIsNone(out_dict[self.dev1_id][0])
        self.assertIsNone(out_dict[self.dev2_id][0])

        # Check error info values
        self.assertEqual(1, out_dict[self.dev1_id][1].errno)
        self.assertEqual(1, out_dict[self.dev2_id][1].errno)
        self.assertEqual("an error message", out_dict[self.dev1_id][1].message)
        self.assertEqual("an error message", out_dict[self.dev2_id][1].message)

if __name__ == '__main__':
    unittest.main()
