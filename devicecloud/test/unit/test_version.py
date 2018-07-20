import unittest

from devicecloud.version import __version__


class TestVersion(unittest.TestCase):

    def test_version_format(self):
        self.assertTrue(len(__version__.split('.')) >= 3)
