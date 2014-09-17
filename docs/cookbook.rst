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

Using Streams
^^^^^^^^^^^^^^

**Description:**

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
