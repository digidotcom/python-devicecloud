Python Device Cloud Library
===========================

[![Build Status](https://travis-ci.org/digidotcom/python-devicecloud.svg?branch=master)](https://travis-ci.org/digidotcom/python-devicecloud)
[![Coverage Status](https://img.shields.io/coveralls/digidotcom/python-devicecloud.svg)](https://coveralls.io/r/digidotcom/python-devicecloud)
[![Code Climate](https://img.shields.io/codeclimate/github/digidotcom/python-devicecloud.svg)](https://codeclimate.com/github/digidotcom/python-devicecloud)
[![Latest Version](https://img.shields.io/pypi/v/devicecloud.svg)](https://pypi.python.org/pypi/devicecloud/)
[![License](https://img.shields.io/badge/license-MPL%202.0-blue.svg)](https://github.com/digidotcom/python-devicecloud/blob/master/LICENSE)

Be sure to check out the [full documentation](http://digidotcom.github.io/python-devicecloud). A [Changelog](https://github.com/digidotcom/python-devicecloud/blob/master/CHANGELOG.md) is also available.

Overview
--------

Python-devicecloud is a library providing simple, intuitive access to [Digi Device Cloud(sm)](http://www.digi.com/products/cloud/digi-device-cloud) for clients written in Python.

The library wraps Device Cloud's REST API and hides the details of forming HTTP requests in order to gain access to device information, file data, streams, and other features of Device Cloud. The API can be found [here](http://ftp1.digi.com/support/documentation/90002008_redirect.htm).

The primary target audience for this library is individuals interfacing with Device Cloud from the server side or developers writing tools to aid device development. For efficient connectivity from devices, we suggest that you first look at using the [Device Cloud Connector](http://www.digi.com/support/productdetail?pid=5575). That being said, this library could also be used on devices if deemed suitable.

Example
-------

The library provides access to a wide array of features, but here is a couple quick examples to give you a taste of what the API looks like.

```python
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
```

For more examples and detailed documentation, be sure to checkout out the [Full API Documentation](https://digidotcom.github.io/python-devicecloud).

Installation
------------

This library can be installed using [pip](https://github.com/pypa/pip). Python versions 2.7+ and 3+ are supported by the library.

```sh
pip install devicecloud
```

If you already have an older version of the library installed, you can upgrade to the latest version by doing

```sh
pip install --upgrade devicecloud
```

Supported Features
------------------

Eventually, it is hoped that there will be complete feature parity between Device Cloud API and this library.  For now, however, that is not the case.  The current features are supported by the library:

* Getting basic device information via DeviceCore
* Provision and Delete devices via DeviceCore
* Listing devices associated with a device cloud account
* Interacting with Device Cloud Data Streams
  * Create Streams
  * Get Stream (by id)
  * List all streams
  * Get metadata for a stream
  * Write a single datapoint to a stream
  * Write many datapoints to a stream (homogeneous bulk write)
  * Write many datapoints to multiple streams (heterogeneous bulk write)
  * Read data points from a stream (includes control over order of
    returned data set as well as allowing for retrieving data
    roll-ups, etc.)
* Support for accessing Device Cloud FileData store
  * Get filedata matching a provided condition (path, file extension,
    size, etc.)
  * Write files to filedata store
  * Recursively walk filedata directory tree from some root location
  * Get full metadata and contents of files and directories.
* Low level support for performing basic SCI commands with limited parsing
  of results and support for only a subset of available services/commands.
* APIs to make direct web service calls to Device Cloud with some details
  handled by the library (see DeviceCloudConnection and 'ws' documentation)
* Device Provisioning via Mac Address, IMEI or Device ID
* Monitors
* Creating a TCP or HTTP monitor

The following features are *not* supported at this time.  Feedback on
which features should be highest priority is always welcome.

* Alarms
* Scheduled Operations
* Asynchronous SCI requests
* High level access to many SCI/RCI operations
* DeviceMetaData
* DeviceVendor
* FileDataHistory
* NetworkInterface support
* XBee specific support (XBeeCore)
* Smart Energy APIs
* SMS Support
* SM/UDP Support
* Carrier Information Access

Contributing
------------

Contributions to the library are very welcome in whatever form can be provided.  This could include issue reports, bug fixes, or features additions.  For issue reports, please [create an issue against the Github project](https://github.com/digidotcom/python-devicecloud/issues).

For code changes, feel free to fork the project on Github and submit a pull request with your changes.  Additional instructions for developers contributing to the project can be found in the [Developer's Guide](https://github.com/digidotcom/python-devicecloud/blob/master/CONTRIBUTING.md).

License
-------

This software is open-source software.

Copyright (c) 2015-2018 Digi International Inc.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed with this file, you can obtain one at http://mozilla.org/MPL/2.0/.

Digi, Digi International, the Digi logo, the Digi website, Digi Device Cloud, Digi Remote Manager, and Digi Cloud Connector are trademarks or registered trademarks of Digi International Inc. in the United States and other countries worldwide. All other trademarks are the property of their respective owners.

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
