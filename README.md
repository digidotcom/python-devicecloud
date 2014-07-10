# Python Device Cloud API
A verbose library for making web service calls to the [Etherios Device Cloud](https://login.etherios.com).

Installation
------------

This library can be installed using [pip](https://github.com/pypa/pip).

```sh
pip install python-devicecloud
```

Overview
--------

Python-devicecloud is a library providing simple, intuitive access to
the [Device Cloud by Etherios](http://www.etherios.com/products/devicecloud/) for clients written in
Python.

The library wraps the Device Cloud REST API and hides the details of forming HTTP requests in order to gain access to device information,
file data, streams, and other features of the device cloud.  The API
wrapped can be found [here](http://ftp1.digi.com/support/documentation/90002008_redirect.htm).


The primary target audience for this library is individuals
interfacing with the device cloud from the server side or developers
writing tools to aid device development.  For efficient connectivity
from devices, we suggest that you first look at using the [Device Cloud
Connector](http://www.etherios.com/products/devicecloud/connector).
That being said, this library could also be used on devices if deemed
suitable.

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
    for device in dc.devicecore.list_devices():
        if device.is_connected():
            print device.get_mac()

    # get the name and current value of all data streams having values
    # with a floating point type
    #
    # This is done using the device cloud stream functionality
    for stream in dc.streams.get_streams():
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

License
-------

This software is open-source software.

Copyright (c) 2014, Etherios, Inc. All rights reserved.
Etherios, Inc. is a Division of Digi International.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this file,
you can obtain one at http://mozilla.org/MPL/2.0/.

Digi, Digi International, the Digi logo, the Digi website, Etherios,
the Etherios logo, the Etherios website, Device Cloud by Etherios, and
Etherios Cloud Connector are trademarks or registered trademarks of
Digi International, Inc. in the United States and other countries
worldwide. All other trademarks are the property of their respective
owners.

THE SOFTWARE AND RELATED TECHNICAL INFORMATION IS PROVIDED "AS IS"
WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL DIGI OR ITS
SUBSIDIARIES BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION IN CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE AND TECHNICAL INFORMATION
HEREIN, INCLUDING ALL SOURCE AND OBJECT CODES, IRRESPECTIVE OF HOW IT
IS USED. YOU AGREE THAT YOU ARE NOT PROHIBITED FROM RECEIVING THIS
SOFTWARE AND TECHNICAL INFORMATION UNDER UNITED STATES AND OTHER
APPLICABLE COUNTRY EXPORT CONTROL LAWS AND REGULATIONS AND THAT YOU
WILL COMPLY WITH ALL APPLICABLE UNITED STATES AND OTHER COUNTRY EXPORT
LAWS AND REGULATIONS WITH REGARD TO USE AND EXPORT OR RE-EXPORT OF THE
SOFTWARE AND TECHNICAL INFORMATION.
