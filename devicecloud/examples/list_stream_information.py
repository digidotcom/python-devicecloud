from devicecloud import DeviceCloud

dc = DeviceCloud('paulosborne', 'X0aD$0@#fxHE')
streams = dc.get_streams_api()
streams.create_data_stream(
    stream_id="test",
    data_type='float',
    description='some description',
)
streams.create_data_stream(
    stream_id="another/test",
    data_type="INTEGER",
    description="Some Integral Thing"
)
print streams.get_stream("test").get_data_type(False)
