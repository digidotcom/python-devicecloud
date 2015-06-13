# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.

from devicecloud.examples.example_helpers import get_authenticated_dc
from devicecloud.filedata import fd_path
import six

if __name__ == '__main__':
    dc = get_authenticated_dc()

    dc.filedata.write_file("/~/test_dir/", "test_file.txt", six.b("Helllo, world!"), "text/plain")
    dc.filedata.write_file("/~/test_dir/", "test_file2.txt", six.b("Hello, again!"))

    for dirpath, directories, files in dc.filedata.walk("/"):
        for fd_file in files:
            print(fd_file)

    for fd in dc.filedata.get_filedata(fd_path == "~/"):
        print (fd)
