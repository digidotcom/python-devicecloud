python-devicecloud
******************

Documention Map
===============

.. toctree::
   :maxdepth: 1

   core
   devicecore
   streams
   filedata
   sci
   filesystem
   monitor
   ws
   cookbook

Introduction
============

Python-devicecloud is a library providing simple, intuitive access to
the `Digi Device Cloud
<http://www.digi.com/products/cloud/digi-device-cloud/>`_ for clients written
in Python.

The library wraps Device Cloud REST API and hides the details of
forming HTTP requests in order to gain access to device information,
file data, streams, and other features of Device Cloud.  The API
wrapped can be found `here
<http://ftp1.digi.com/support/documentation/90002008_redirect.htm>`_.


The primary target audience for this library is individuals
interfacing with Device Cloud from the server side or developers
writing tools to aid device development.  For efficient connectivity
from devices, we suggest that you first look at using the `Device
Cloud Connector <http://www.digi.com/support/productdetail?pid=5575>`_.
That being said, this library could also be used on devices if deemed
suitable.

The library provides access to a wide array of features, but here is a
quick example of what the API looks like::

    from devicecloud import DeviceCloud

    dc = DeviceCloud('user', 'pass')

    # show the MAC address of all devices that are currently connected
    #
    # This is done using Device Cloud DeviceCore functionality
    print "== Connected Devices =="
    for device in dc.devicecore.get_devices():
        if device.is_connected():
            print device.get_mac()

    # get the name and current value of all data streams having values
    # with a floating point type
    #
    # This is done using Device Cloud stream functionality
    for stream in dc.streams.get_streams():
        if stream.get_data_type().lower() in ('float', 'double'):
            print "%s -> %s" % (stream.get_stream_id(), stream.get_current_value())

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

