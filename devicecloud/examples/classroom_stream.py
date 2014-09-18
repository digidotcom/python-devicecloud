from devicecloud import DeviceCloud
import json
from devicecloud.streams import STREAM_TYPE_STRING, DataPoint
from getpass import getpass


def get_authenticated_dc():
    while True:
        user = raw_input("username: ")
        password = getpass("password: ")
        dc = DeviceCloud(user, password,
                         base_url="https://login-etherios-com-2v5p9uat81qu.runscope.net")
        if dc.has_valid_credentials():
            print ("Credentials accepted!")
            return dc
        else:
            print ("Invalid username or password provided, try again")


dc = get_authenticated_dc()

classroom = dc.streams.get_stream_if_exists('classroom')
if not classroom:
    classroom = dc.streams.create_stream(
        stream_id='classroom',
        data_type=STREAM_TYPE_STRING,
        description='Stream representing a classroom of students',
    )

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
print json.loads(most_recent_dp.get_data())['name']