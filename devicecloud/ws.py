# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.
import functools
import inspect


class WebServiceStub(object):
    """Provide a set of methods to directory access the web services API at a given path

    Web services stubs can be chained in order to build a path and, eventually, perform
    an operation on the end result.  For instance, the following will perform
    a GET request on the path ``/some/base/with/some/added/stuff``::

        WebServiceStub(conn, "/some/base").with.some.added.stuff.get()

    In the context of the this library, a more common example might be accessing
    a V1 API such as /ws/v1/devices.  That would be done like this::

        response = dc.ws.v1.devices.get()

    Where response would end up being a `requests Response object
    <http://docs.python-requests.org/en/latest/api/#requests.Response>`.

    Any of the methods exposed by :class:`devicecloud.DeviceCloudConnection` may be
    called and the path for the stub will be passed as the first argument to
    the method with the same name in that class.

    """

    def __init__(self, conn, path):
        self._conn = conn
        self._path = "/" + path if path[0] != '/' else path

    def __getattr__(self, attr):
        """We implement this method to provide the "builder" syntax"""
        conn_meth = getattr(self._conn, attr, None)
        if conn_meth is not None and inspect.ismethod(conn_meth):
            # If this is method on DeviceCloudConnection, then return a function bound to
            # that method that will be called with this stub's path
            @functools.wraps(conn_meth)
            def bound_cloud_connection_method(*args, **kwargs):
                return conn_meth(self._path, *args, **kwargs)
            return bound_cloud_connection_method

        # Otherwise, assume that specified attribute is another path and return
        # a new builder which is our path combined with the provided attribute
        return WebServiceStub(self._conn, "{}/{}".format(self._path, attr))
