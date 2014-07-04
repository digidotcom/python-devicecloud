python-devicecloud
==================

Introduction
------------

Python-devicecloud is a library providing simple, intuitive access to
the `Device Cloud by Etherios
<http://www.etherios.com/products/devicecloud/>`_ for clients written
in Python.

The library wraps the Device Cloud REST API and hides the details of
forming HTTP requests in order to gain access to device information,
file data, streams, and other features of the device cloud.  The API
wrapped can be found `here
<http://ftp1.digi.com/support/documentation/90002008_redirect.htm>`_.


The primary target audience for this library is individuals
interfacing with the device cloud from the server side or developers
writing tools to aid device development.  For efficient connectivity
from devices, we suggest that you first look at using the `Device
Cloud Connector <http://www.etherios.com/products/devicecloud/connector>`_.
That being said, this library could also be used on devices if deemed
suitable.

The library provides access to a wide array of features, but here is a
quick example of what the API looks like::

    from devicecloud import DeviceCloud

    dc = DeviceCloud('user', 'pass')

    # show the MAC address of all devices that are currently connected
    #
    # This is done using the device cloud DeviceCore functionality
    print "== Connected Devices =="
    for device in dc.list_devices():
        if device.is_connected():
            print device.get_mac()

    # get the name and current value of all data streams having values
    # with a floating point type
    #
    # This is done using the device cloud stream functionality
    for stream in dc.get_streams():
        if stream.get_data_type().lower() in ('float', 'double'):
            print "%s -> %s" % (stream.get_name(), stream.get_current_value())


API Documentation
-----------------

Core API
^^^^^^^^

The `devicecloud.DeviceCloud` class contains the core interface which
will be used by all clients using the devicecloud library.

.. automodule:: devicecloud
   :members:

DeviceCore
^^^^^^^^^^

DeviceCore provides access to core device information such as which
devices are in a given device cloud account, which of those are
connected, etc.

.. automodule:: devicecloud.api.devicecore
   :members:

FileData
^^^^^^^^

The filedata module provides function for reading, writing, and
deleting "files" from the device cloud FileData store.

.. automodule:: devicecloud.api.filedata
   :members:

SCI
^^^

Provide access to the device cloud Server Command Interface used for
sending messages to devices connected to the device cloud.

.. automodule:: devicecloud.api.sci
   :members:

Streams
^^^^^^^

Provides programmatic access to the device cloud streams API.

.. automodule:: devicecloud.api.streams
   :members:


API Documentation
-----------------

Contents:

.. toctree::
   :maxdepth: 2


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

