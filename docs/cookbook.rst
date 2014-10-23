Cookbook
=========

This page is meant to show complete examples for common uses of the library.
For more granular or specific examples of API usage check out the individual API pages.

.. note::

    There are also examples checked into source control under /devicecloud/examples/*_playground.py
    which will provide additional example uses of the library.

Each example will assume an instance of :class:`devicecloud.DeviceCloud` has been
created with something like so::

    dc = DeviceCloud(<username>, <password>)

Streams - Creating Streams and Data Points
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For this example, let's create a DataStream that represents a class room.  As students
enter the classroom there is a DataPoint representing them written to the stream.

First let's get or create the stream::

    classroom = dc.streams.get_stream_if_exists('classroom')
    if not classroom:
        classroom = dc.streams.create_stream(
            stream_id='classroom',
            data_type=STREAM_TYPE_STRING,
            description='Stream representing a classroom of students',
        )

A student named Bob enters the classroom so we write a DataPoint representing Bob
to the stream.  To represent Bob let's use a JSON object::

    student = {
        'name': 'Bob',
        'student_id': 12,
        'age': 21,
    }
    datapoint = DataPoint(data=json.dumps(student))
    classroom.write(datapoint)

Now, two students enter at the same time.  For this we can write both data points
as a batch which only uses one HTTP request (up to 250 data points)::

    students = [
        {
            'name': 'James',
            'student_id': 13,
            'age': 22,
        },
        {
            'name': 'Henry',
            'student_id': 14,
            'age': 20,
        }
    ]
    datapoints = [DataPoint(data=json.dumps(x)) for x in students]
    classroom.bulk_write_datapoints(datapoints)

Finally, let's print the name of the student who most recently entered the classroom::

    most_recent_student = classroom.get_current_value()
    print json.loads(most_recent_student.get_data())['name']  # Prints 'Henry'


Streams - Deleting
^^^^^^^^^^^^^^^^^^^^

Let's delete the classroom stream from the above example so we can start fresh in the
next example::

    classroom.delete()

Streams - Roll-up Data
^^^^^^^^^^^^^^^^^^^^^^^^

Roll-up data is a way to group data points based on time intervals in which they
were written to the cloud.  From our previous example lets figure out which students
entered the classroom throughout the day and which hour they entered.

First let's write some test data to the cloud.  Since roll-ups only work on numerical
data types we will student id's instead of JSON.

Create a new data stream that is of type int::

    classroom = dc.streams.create_stream(
            stream_id='classroom',
            data_type=STREAM_TYPE_INTEGER,
            description='Stream representing a classroom of students (as id's)',
        )

Next is a function that fills the classroom with data points that have randomly
generated timestamp values within the next 24 hours::

    now = time.time()
    one_day_in_seconds = 86400

    datapoints = list()
    for student_id in xrange(100):
        deviation = random.randint(0, one_day_in_seconds)
        random_time = now + deviation
        datapoint = DataPoint(data=student_id,
                              timestamp=datetime.datetime.fromtimestamp(random_time))
        datapoints.append(datapoint)

    classroom.bulk_write_datapoints(datapoints)

Finally, let's figure out which students entered the classroom which hours of the day::

    rollup_data = classroom.read(rollup_interval='hour', rollup_method='count')
    hourly_data = {}
    for dp in rollup_data:
        hourly_data[dp.get_timestamp().hour] = dp.get_data()
    pprint.pprint(hourly_data)

The result is a dictionary where the key's are the hour in the day and the values are the
number of students who entered the classroom that hour::

    {0: 10,
     1: 10,
     2: 9,
     3: 3,
     4: 3,
     5: 6,
     6: 9,
     7: 11,
     8: 5,
     9: 7,
     10: 9,
     11: 9,
     12: 7,
     13: 6,
     14: 13,
     15: 8,
     16: 13,
     17: 9,
     18: 7,
     19: 7,
     20: 11,
     21: 8,
     22: 6,
     23: 11}


Device Core - Groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

    This assumes your device is provisioned.

First, get a reference to the device which you would like to add a specific group::

    device = devicecore.get_device('00:40:9D:50:B0:EA')

Then you can add it to a group and fetch it to make sure it works::

    device.add_to_group('mygroup')
    device.get_group_path()  # prints 'mygroup' (the DC sometimes needs a second to catch up)

Or remove it::

    device.remove_from_group()
