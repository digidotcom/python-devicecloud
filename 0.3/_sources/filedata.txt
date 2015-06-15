FileData API
============

FileData Overview
-----------------

The FileData store on the device cloud provides a hierarchical mechanism for temporarily
storing information in files sent from devices.  With the APIs provided by the device
cloud, it is possible to use the FileData store in a number of different ways to implement
various use cases.

There are two main ways of thinking about the FileData store:

1.  As hierarchical data store for temporarily storing data pushes from devices
2.  As a message queue

The usage for both scenarios is similar.  In the first case, it is likely that a web
service will poll the FileData store for new files matching some criterion on a periodic
basis.  If using the FileData store as a queue, one will likely want to setup monitors
on FileData paths matching certain criterion.  The set of files matching some condition
can then be thought of as a channel.

This library seeks to make using the device cloud for both of these use cases simple
and robust.

Navigating the FileData Store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are a few main ways to navigate the FileData store.

Method 1: Iterate through the file tree by getting the filedata
objects associated with paths or other conditions::

    condtion = (fd_path == '~/')
    for filedata in dc.filedata.get_filedata(condition):
        print filedata

The :meth:`.FileDataAPI.get_filedata` method will return a generator
over the set of FileData directories and files matching the provided
conditions.  The two types availble (which are both instances of
:class:`.FileDataObject` are :class:`.FileDataDirectory` and
:class:`.FileDataFile`.

Other methods of navigating the store are built upon the functionality
provided by :meth:`.FileDataAPI.get_filedata`.

Method 2: The :meth:`.FileDataAPI.walk` method provides a convenient
way to iterate over all files and directories starting with some root
within the filedata store.  This method mimicks the interface and
behavior provided by the python standard library :meth:`os.walk`
which is used to iterate over one's local filesystem.

Here is a basic example::

    for dirname, directories, files in dc.filedata.walk():
        for file in files:
           print file.get_full_path()

It is also possible to perform a walk from a given :class:`.FileDataDirectory`
as follows::

    d = dc.filedata.get_filedata("~/mydevice/mydir")
    for dirname, directories, files in d.walk():
       for file in files:
          print file.get_full_path()


Reading Files and File Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After finding a :class:`.FileDataFile` using either :meth:`.FileDataAPI.get_filedata`
or :meth:`.FileDataAPI.walk`, access to file contents and metadata is provided
by a set of straightforward accessors.  Many of these are also available on
:class:`.FileDataDirectory` objects as well.  Here we show the basic methods::

    # f is a FileDataFile object
    f.get_data()  # the data contained in the file
    f.get_last_modified_date()  # returns datetime object
    f.get_type()  # returns 'file'.  'directory' for directories
    f.get_content_type()  # returns content type (e.g. 'application/xml')
    f.get_customer_id()  # returns customer id (string)
    f.get_created_date()  # returns datetime object
    f.get_name()  # returns name of file (e.g. test.txt)
    f.get_path()  # returns path leading up to the file (e.g. /a/b/c)
    f.get_full_path()  # returns full path including name (e.g. /a/b/c/test.txt)
    f.get_size()  # returns the size of the file in bytes as int


Creating a Directory
~~~~~~~~~~~~~~~~~~~~

TODO: This functionality is not current active.

There are three ways to create a new directory:

1. Create full path with :meth:`.FileDataAPI.make_dirs`.  This will recursively
   create the full path specified.
2. Write a file to a directory that does not yet exist.  If the path is valid,
   all directories should be created recursively.
3. By calling :meth:`.FileDataDirectory.add_subdirectory`

Different methods may suit your needs depending on your use cases.

Writing a File
~~~~~~~~~~~~~~

The following methods may be used to write a file:

1. Use :meth:`.FileDataAPI.write_file`.  This requires a full path to be specified.
2. Use :meth:`.FileDataDirectory.write_file`.  As you already have a directory path
   in that case, you do not need to specify the path leading to the file.

Here's a basic example::

    dc.filedata.write_file(
        path="~/test",
        name="test.json",
        content_type="application/json",
        archive=False
    )

Viewing File History
~~~~~~~~~~~~~~~~~~~~

.. note:: Support for programmatically getting history for files is not
         supported at this time.

API Documentation
-----------------

The filedata module provides function for reading, writing, and
deleting "files" from the device cloud FileData store.

.. automodule:: devicecloud.filedata
   :members:
