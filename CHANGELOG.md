## Python Devicecloud Library Changelog

### 0.1.1 / 2014-09-14
[Full Changelog](https://github.com/etherios/python-devicecloud/compare/0.1...0.1.1)

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
