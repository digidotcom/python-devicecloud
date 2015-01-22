import unittest

from devicecloud import DeviceCloudException
from mock import MagicMock, patch

from devicecloud.ws import WebServiceStub
from devicecloud import DeviceCloudConnection


class MockConnection(MagicMock):

    def get(self, *args, **kwargs):
        return (args, kwargs)

    def post(self, *args, **kwargs):
        return (args, kwargs)


class LegacyAPIMemberInternalsTests(unittest.TestCase):

    def setUp(self):
        self.conn = MockConnection()
        self.stub = WebServiceStub(self.conn, '/ws')

    def test_path_building(self):
        test = self.stub.a.b.c
        self.assertEqual(test._path, "/ws/a/b/c")

    def test_method_access(self):
        res = self.stub.a.b.c.get()
        self.assertEqual(res[0], ("/ws/a/b/c", ))
        self.assertDictEqual(res[1], {})

    def test_method_access_args_kwargs(self):
        res = self.stub.a.test.path.post("foo", bar="baz")
        self.assertEqual(res[0], ("/ws/a/test/path", "foo"))
        self.assertDictEqual(res[1], {"bar": "baz"})

if __name__ == '__main__':
    unittest.main()
