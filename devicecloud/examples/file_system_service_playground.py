import six
from devicecloud.examples.example_helpers import get_authenticated_dc
from devicecloud.file_system_service import FileSystemServiceAPI
from devicecloud.sci import DeviceTarget


def use_filesystem(dc, target, base_dir):
    fssapi = dc.get_fss_api()
    fd = dc.get_filedata_api()

    tmp_file = '{}/test.txt'.format(base_dir)
    tmp_str = six.b('testing string')

    print("\nWriting temp file {}".format(tmp_file))
    print(fssapi.put_file(target, tmp_file, file_data=tmp_str))

    tmp_server_file = 'test_file.txt'
    print("\nWriting temp file to server {}".format(tmp_server_file))
    fd.write_file("/~/test_dir/", "test_file.txt", six.b("Hello, world!"), "text/plain")

    tmp_server_device_file = '{}/{}'.format(base_dir, tmp_server_file)
    print("\nWriting temp file from server {}".format(tmp_server_device_file))
    fssapi.put_file(target, tmp_server_device_file, server_file='/~/test_dir/{}'.format(tmp_server_file))

    print("\nList of files in {}".format(base_dir))
    out_dict = fssapi.list_files(target, base_dir)
    print(out_dict)

    for device, (dirs, files) in out_dict.iteritems():
        for f in files:
            if f.path.endswith('test.txt'):
                print("\nUsing file info object to get data")
                print(f.get_data())

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

    print("\nDeleting temp file")
    print(fssapi.delete_file(target, tmp_file))
    print(fssapi.delete_file(target, tmp_server_device_file))

    print("\nList of files in {}".format(base_dir))
    out_dict = fssapi.list_files(target, base_dir)
    print(out_dict)


if __name__ == "__main__":
    dc = get_authenticated_dc()
    device_id = "your-device-id-here"
    target = DeviceTarget(device_id)
    base_dir = '/a/directory/on/your/device'
    use_filesystem(dc, target, base_dir)
