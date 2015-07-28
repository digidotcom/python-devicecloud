import time
import six
from devicecloud.examples.example_helpers import get_authenticated_dc
from devicecloud.file_system_service import ErrorInfo, FileSystemServiceCommandBlock, LsCommand, PutCommand
from devicecloud.sci import DeviceTarget


def put_test_file(fssapi, target, tmp_file_path):
    tmp_str = six.b('testing string')

    print("\nWriting test file {}".format(tmp_file_path))
    print(fssapi.put_file(target, tmp_file_path, file_data=tmp_str))


def list_contents(fssapi, target, dev_dir):
    print("\nList of files in {}".format(dev_dir))
    out_dict = fssapi.list_files(target, dev_dir)
    print("list_files returned: {}".format(str(out_dict)))
    print_list_contents(out_dict)


def print_list_contents(out_dict):
    print("\nPrint each item from list_files:")
    for device_id, device_data in six.iteritems(out_dict):
        print("Items from device {}".format(device_id))
        if isinstance(device_data, ErrorInfo):
            print("    ErrorInfo: {}".format(device_data))
        else:
            (dirs, files) = device_data
            if len(dirs) + len(files) == 0:
                print "    None"
            for d in dirs:
                print("    Directory: {}".format(str(d)))
            for f in files:
                print("    File: {}".format(str(f)))


def delete_test_file(fssapi, target, tmp_file_path):
    print("\nDeleting test file: {}".format(tmp_file_path))
    print(fssapi.delete_file(target, tmp_file_path))


def get_modified_files(fssapi, target, dev_dir, last_modified_cutoff):
    print("\nGetting all files modified since {}".format(last_modified_cutoff))
    out_dict = fssapi.get_modified_items(target, dev_dir, last_modified_cutoff)
    print_list_contents(out_dict)


def use_filesystem(dc, target, base_dir):
    fssapi = dc.get_fss_api()
    fd = dc.get_filedata_api()

    tmp_file = '{}/test.txt'.format(base_dir)

    put_test_file(fssapi, target, tmp_file)

    tmp_server_file = 'test_file.txt'
    print("\nWriting temp file to server {}".format(tmp_server_file))
    fd.write_file("/~/test_dir/", "test_file.txt", six.b("Hello, world!"), "text/plain")

    tmp_server_device_file = '{}/{}'.format(base_dir, tmp_server_file)
    print("\nWriting temp file from server {}".format(tmp_server_device_file))
    fssapi.put_file(target, tmp_server_device_file, server_file='/~/test_dir/{}'.format(tmp_server_file))

    list_contents(fssapi, target, base_dir)

    print("\nUsing API to get file data")
    print(fssapi.get_file(target, tmp_file))

    print("\nUsing API to get other file data")
    print(fssapi.get_file(target, tmp_server_device_file))

    print("\nUsing API to get partial file data")
    print(fssapi.get_file(target, tmp_file, offset=3, length=4))

    print("\nUsing API to write part of a file")
    fssapi.put_file(target, tmp_file, file_data=six.b("what"), offset=4)
    print(fssapi.get_file(target, tmp_file))

    print("\nUsing API to write part of a file and truncating")
    fssapi.put_file(target, tmp_file, file_data=six.b("why"), offset=4, truncate=True)
    print(fssapi.get_file(target, tmp_file))

    delete_test_file(fssapi, target, tmp_file)
    delete_test_file(fssapi, target, tmp_server_device_file)

    print("\nList of files in {}".format(base_dir))
    out_dict = fssapi.list_files(target, base_dir)
    print(out_dict)


if __name__ == "__main__":
    dc = get_authenticated_dc()
    device_id = "your-device-id-here"
    target = DeviceTarget(device_id)
    base_dir = '/a/directory/on/your/device'
    use_filesystem(dc, target, base_dir)

    fssapi = dc.get_fss_api()
    tmp_file_path = "{}/{}".format(base_dir, 'test_file.txt')
    put_test_file(fssapi, target, tmp_file_path)
    cutoff_time = time.time()
    get_modified_files(fssapi, target, base_dir, cutoff_time)
    print("\nModifying file {}".format(tmp_file_path))
    fssapi.put_file(target, tmp_file_path, file_data=six.b("data"), offset=4)
    time.sleep(5)
    get_modified_files(fssapi, target, base_dir, cutoff_time)
    delete_test_file(fssapi, target, tmp_file_path)

    command_block = FileSystemServiceCommandBlock()
    command_block.add_command(LsCommand(base_dir))
    command_block.add_command(LsCommand('/another/directory/on/your/device'))

    print(fssapi.send_command_block(target, command_block))
