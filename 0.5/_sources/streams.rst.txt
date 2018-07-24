Streams API
===========

Streams Overview
----------------

Data Streams on Device Cloud provide a mechanism for storing time-series
values over a long period of time.  Each individual value in the time series
is known as a Data Point.

There are a few basic operations supported by Device Cloud on streams which
are supported by Device Cloud and this library.  Here we give examples of
each.

Listing Streams
^^^^^^^^^^^^^^^

Although it is not recommended for production applications, it is often useful
when building tools to be able to fetch a list of all streams.  This can be
done by using :meth:`.StreamsAPI.get_streams`::

    dc = DeviceCloud('user', 'pass')
    for stream in dc.streams.get_streams():
        print "%s: %s" % (stream.get_stream_id(),
                          stream.get_description())

Creating a Stream
^^^^^^^^^^^^^^^^^

Streams can be created in two ways, both of which are supported by this library.

1. Create a stream explicitly using :meth:`.StreamsAPI.create_stream`
2. Get a reference to a stream using :meth:`.StreamsAPI.get_stream`
   that does not yet exist and write a datapoint to it.

Here's examples of these two methods for creating a new stream::

    dc = DeviceCloud('user', 'pass')

    # explicitly create a new data stream
    humidity_stream = dc.streams.create_stream(
        stream_id="mystreams/hudidity",
        data_type="float",
        description="Humidity")
    humidity_stream.write(Datapoint(81.2))

    # create data stream implicitly
    temperature_stream = streams.get_stream("/%s/temperature" % some_id)
    temperature_stream.write(Datapoint(
            stream_id="mystreams/temperature" % some_id,
            data=74.1,
            description="Outside Air Temperature in F",
            data_type=STREAM_TYPE_FLOAT,
            unit="Degrees Fahrenheit"
    ))

Getting Information About A Stream
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Whether we know a stream by id and have gotten a reference using
:meth:`.StreamsAPI.get_stream` or have discovered it using
:meth:`.StreamsAPI.get_streams`, the :class:`.DataStream` should
be able to provide access to all metadata about the stream that
you may need.  Here we show several of them::

    strm = dc.streams.get_stream("test")
    print strm.get_stream_id()
    print strm.get_data_type()
    print strm.get_units()
    print strm.get_description()
    print strm.get_data_ttl()
    print strm.get_rollup_ttl()
    print strm.get_current_value()  # return DataPoint object

.. note::

   :meth:`.DataStream.get_current_value()` does not use cached values by
   default and will make a web service call to get the most recent current
   value unless ``use_cached`` is set to True when called.

Deleting a Stream
^^^^^^^^^^^^^^^^^

Deleting a data stream is possible by calling :meth:`.DataStream.delete`::

    strm = dc.streams.get_stream("doomed")
    strm.delete()

Updating Stream Metadata
^^^^^^^^^^^^^^^^^^^^^^^^

This feature is currently not supported.  Some stream information may
be updated by writing a :class:`.DataPoint` and including updated
stream info elements.

DataPoint objects
^^^^^^^^^^^^^^^^^

The :class:`.DataPoint` class encapsulates all information required for
both writing data points as well as retrieving information about data
points stored on Device Cloud.

API Documentation
-----------------

.. automodule:: devicecloud.streams
   :members:
