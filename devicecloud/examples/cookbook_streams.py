import datetime
import pprint
import random
import time
import json

from devicecloud.examples.example_helpers import get_authenticated_dc

from devicecloud.streams import STREAM_TYPE_STRING, DataPoint, STREAM_TYPE_INTEGER


def get_or_create_classroom(datatype):
    dc = get_authenticated_dc()
    classroom = dc.streams.get_stream_if_exists('classroom')
    if not classroom:
        classroom = dc.streams.create_stream(
            stream_id='classroom',
            data_type=datatype,
            description='Stream representing a classroom of students',
        )
    return classroom


def fill_classroom_with_student_ids(classroom):
    # fake data with wide range of timestamps
    now = time.time()
    one_day_in_seconds = 86400

    datapoints = list()
    for student_id in xrange(100):
        deviation = random.randint(0, one_day_in_seconds)
        random_time = now + deviation
        datapoint = DataPoint(data=student_id,
                              timestamp=datetime.datetime.fromtimestamp(random_time),
                              data_type=STREAM_TYPE_INTEGER)
        datapoints.append(datapoint)

    classroom.bulk_write_datapoints(datapoints)


def example_1():
    classroom = get_or_create_classroom(STREAM_TYPE_STRING)

    student = {
        'name': 'Bob',
        'student_id': 12,
        'age': 21,
    }
    datapoint = DataPoint(data=json.dumps(student))
    classroom.write(datapoint)

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

    most_recent_dp = classroom.get_current_value()
    print(json.loads(most_recent_dp.get_data())['name'])


def example_2():
    # assume `fill_classroom_with_random_data()` has already been called

    classroom = get_or_create_classroom(STREAM_TYPE_INTEGER)
    rollup_data = classroom.read(rollup_interval='hour', rollup_method='count')
    hourly_data = {}
    for dp in rollup_data:
        hourly_data[dp.get_timestamp().hour] = dp.get_data()
    pprint.pprint(hourly_data)


example_2()
print('done.')
