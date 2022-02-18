## Python Devicecloud Library Changelog


### 0.5.9 / 2021-02-18
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.5.8...0.5.9)

Enhancement:

* core: update other dependecies to "compatible" versions on install


### 0.5.8 / 2021-02-17
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.5.7...0.5.8)

Enhancement:

* datastreams: add "GEOJSON" format type to DataStreams


### 0.5.7 / 2020-04-22
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.5.6...0.5.7)

Enhancement:

* update requests dependency to 2.20
* update other dependecies to "compatible" versions on install


### 0.5.6 / 2019-07-24
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.5.5...0.5.6)

Enhancement:

* core: update package long description

### 0.5.5 / 2019-07-23
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.5.4...0.5.5)

Enhancement:

* core: remove subprocess during installation (make installation Windows compatible)


### 0.5.4 / 2019-05-22
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.5.3...0.5.4)

Enhancement:

* tests: added test for sci firmware update attributes


### 0.5.3 / 2018-07-24
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.5.1...0.5.3)

Enhancements:

* devicecore: add support for adding multiple tags


### 0.5.1 / 2018-07-20
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.5.0...0.5.1)

Changes:

* pypi: upgrade Development Status to "4 - Beta"


### 0.5.0 / 2018-07-20
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.4.3...0.5.0)

Enhancements:

* devicecore: add support for adding and removing tags from a device


### 0.4.3 / 2018-06-11
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.4.2...0.4.3)

Bug Fixes:

* core: updated Device Cloud CRT to latest
* core: updated requirements to latest

### 0.4.2 / 2015-11-20
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.4.1...0.4.2)

Bug Fixes:

* core: All Etherios references have been replaced with Digi.  Most
  importantly, the default URL for the devicecloud is now
  devicecloud.digi.com.  The old URL may not redirect properly at some
  point in the future.

### 0.4.1 / 2015-11-13
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.4...0.4.1)

Bug Fixes:

* sci: Targetting groups now works

### 0.4 / 2015-10-01
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.3...0.4)

Enhancements:

* monitors: basic support for creating HTTP monitors was added
* streams: support for the JSON data type added
* sci: support added for filesystem service added.  This allows you to
  access files and directories on any device supporting this service.

Bug Fixes:

* streams: fix data translations from device cloud <-> python types
  when reading and writing data points.  See
  https://github.com/digidotcom/python-devicecloud/commit/5ac6c15cddf010709361c16b69e622aca93d6b28

### 0.3 / 2015-06-15
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.2...0.3)

Enhancements:

* monitor: Support for the Monitor API was added allowing for
  querying, adding, and removing of monitors (limiited to TCP right
  now).
* monitor: Support for listening for changes and receiving callbacks
  when monitors are triggered has been added.  Support is limited to
  SSL/TCP for now.
* streams: get_stream() now optionally accepts a ``stream_prefix``
  that allow for restricting which streams are returned based on path.
* sci: support added for ``get_job_async``
* devicecore: provisioning: support added for removing devices from an
  account.
* core: HTTP sessions are now used in order to allow for HTTP
  connection reuse and credential reuse (via cookies)

Bug Fixes:

* Unit tests for fixed for Python 3.4
* filedata: ``raw`` option added to work around some issues when
  retrieving binary data as base64

### 0.2 / 2015-01-23
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.1.1...0.2)

Enhancements:

* Integration tests were added for some APIs to further test library correctness
* Documentation for several parts of the system, including streams
  was enhanced.
* Several APIs now support pagination on large result sets that previously lacked support.
* We now expose the underlying object used to send device cloud API requests via
  `dc.get_connection()`.  This allows users to more easily talk to currently unsupported
  APIs.  Support for the basic API verbs plus helpers for handling pagination and other
  concerns are included.
* Support for group operations in devicecore is now present
* Filedata files and directories can now be deleted
* A new 'ws' API has been added for making direct web service requests
* DeviceCore now has support for provisioning one or multiple devices

API Changes:

* devicecore: `list_devices` was changed to `get_devices`.  Previously, the
  code did not match the documentation on this front.  Calls to `dc.devicecore.list_devices`
  will need to be changed to `dc.devicecore.get_devices`

Bug Fixes:

* streams: When creating a stream, the stream_id was used for the description rather
  than the provided description.
* core: Library now freezes dependencies.  Several dependencies updated to latest
  versions (e.g. requests).  Without this, some combinations of the library
  and dependencies caused various errors.

Thanks to Dan Harrison, Steve Stack, Tom Manley, and Paul Osborne for contributions
going into this release.

### 0.1.1 / 2014-09-14
[Full Changelog](https://github.com/digidotcom/python-devicecloud/compare/0.1...0.1.1)

Enhancements:

* Additional badges were added to the main README
* Documentation updates and improvements
* Packaging was improved to not valid DRY with version

Bug Fixes:

* PYTHONDC-90: Restructured text is now included with sdist releases.  This removes
  an unsightly warning when installing the package.
* PYTHONDC-91: Mismatches between the documentation and code were fixed.

### 0.1 / 2014-09-12
The initial version of the library was released into the world.  This version
supported the following features:

* Getting basic device information via DeviceCore
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
