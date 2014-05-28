Python Devicecloud API
======================

Overview
--------

Python-devicecloud is a library providing simple, intuitive access to
the Device Cloud by Etherios
(http://www.etherios.com/products/devicecloud/) for clients written in
Python.

The library wraps the Device Cloud REST API and hides the details of
forming HTTP requests in order to gain access to device information,
file data, streams, and other features of the device cloud.  The API
wrapped can be found here:
http://ftp1.digi.com/support/documentation/90002008_redirect.htm

The primary target audience for this library is individuals
interfacing with the device cloud from the server side or developers
writing tools to aid device development.  For efficient connectivity
from devices, we suggest that you first look at using the Device Cloud
Connector: http://www.etherios.com/products/devicecloud/connector.
That being said, this library could also be used on devices if deemed
suitable.

License
-------

This library is released as open source under the Mozile Public
License v2.0.  Please see the LICENSE file for additional details.

Example
-------

The library provides access to a wide array of features, but here is a
couple quick examples to give you a taste of what the API looks like.

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


Supported Features
------------------

Eventually, it is hoped that there will be complete feature parity
between the device cloud API and this library.  For now, however, that
is not the case.  The current features are supported by the library:

* Getting basic device information via DeviceCore
* Setting some information on device via DeviceCore
* Performing simple operations on FileData
* Accessing, Creating, Pushing Data Into, and Deleting Data Streams
* Low level support for performing basic SCI commands with limited parsing
  of results and support for only a subset of available services/commands.

The following features are *not* supported at this time:

* Alarms
* Monitors
* Scheduled Operations
* Creating a TCP or HTTP monitor
* Asynchronous SCI requests
* High level access to many SCI/RCI operations
* DeviceMetaData
* DeviceVendor
* FileDataHistory
* Group Operations (CRUD)
* NetworkInterface support
* XBee specific support (XBeeCore)
* Device Provisioning
* Smart Energy APIs
* SMS Support
* Satellite/Iridium Support
* SM/UDP Support
* Carrier Information Access

Roadmap and History
--------------------

Roadmap TBD
