Direct Web Services API
=======================

The Device Cloud exposes a large set of functionality to users and the
python-devicecloud library seeks to provide convenient and complete
APIs for a majority of these.  However, there are APIs which the library
does not cover; some may have coverage in the future and others may never
have direct support in the library.

The "ws" API provides a mechanism for directly making calls to
unsupported web services APIs.  An example of the syntax exposed by the library
is probably best demonstrated with an example.

An example of an API not currently supported by the library is the `Alarms API
<http://ftp1.digi.com/support/documentation/html/90002008/90002008_R/Default.htm#Programming Topics/Alarms.htm#AlarmAPI%3FTocPath%3DDevice%2520Cloud%2520Programming%2520Guide%7CAlarms%7C_____1>`_.
This API is a "legacy" API (it is not prefixed with a "v1") and its basic interface is GET, POST, PUT, and
DELETE of the path "/ws/Alarm".  The API returns response and expects payloads to be in XML according
to a format described in the documentation::

    # List alarms
    #
    # Retrieves results of GET to /ws/Alarms with authentication and will raise
    # the standard exceptions in the case of a failure response.
    #
    >>> dc = devicecloud.DeviceCloud('user', 'pass')
    >>> response = dc.ws.Alarm.get()
    >>> print response.content
    ... A bunch of XML ...
    >>> print dc.ws.Alarm.get_json()
    ... A bunch of JSON ...
    >>> print list(dc.ws.Alarm.iter_json_pages())
    ... All Alarms over all pages with result as list of dictionaries ...

    #
    # Note that in the syntactic sugar may fall short.  In those cases, you
    # may need to fall back to using the underlying DeviceConnection
    #
    >>> alarm_id = 10
    >>> print dc.get_connection().get_json("/ws/Alarm/{}".format(alarm_id))
    ... Some JSON ...

For more details, refer to the documentation on the methods for :py:class:`devicecloud.DeviceCloudConnection`.
