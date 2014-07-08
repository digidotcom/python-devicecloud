# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from devicecloud import DeviceCloud

dc = DeviceCloud('USER', "PASSWORD")  # TODO: replace

streams = dc.get_streams_api()
streams.create_stream(
    stream_id="test",
    data_type='float',
    description='some description',
)
streams.create_stream(
    stream_id="another/test",
    data_type="INTEGER",
    description="Some Integral Thing"
)
print streams.get_stream("test").get_data_type(False)
