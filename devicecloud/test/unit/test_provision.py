"""
Tests the provisioning feature of the devicecore.

Isolated to its own file, because it's so different from everything else.
"""
import sys
import unittest

import mock

from devicecloud import DeviceCloudHttpException
from devicecloud.devicecore import DeviceCoreAPI
from devicecloud.test.unit.test_utilities import HttpTestBase

SUCCESS_STATUS = 201
ERRORS_STATUS = 207


def build_response(response_list):
    """
    Generate response from an expected result.

    Just a utility function for convenience.
    """
    if type(response_list) == dict:
        response_list = [response_list]
    xml_tags = [r['error'] and
                '<error>' + r['error'] + '</error>' or
                '<location>' + r['location'] + '</location>'
                for r in response_list]
    return '<?xml version="1.0" encoding="ISO-8859-1"?>\n<list>' + ''.join(xml_tags) + '</list>'


class ProvisioningParserTests(HttpTestBase):
    def test_xml_error(self):
        # Make sure that if their interface changes, and suddenly the XML stuff
        # stops working, that an exception will indeed be thrown.
        self.prepare_response('POST', '/ws/DeviceCore', 'Bad Request', status=400)
        try:
            self.dc.devicecore._provision(['<device>whatever</device>'])
        except DeviceCloudHttpException:
            pass
        else:
            assert False, "should have thrown exception"
        self.prepare_response('POST', '/ws/DeviceCore', 'Internal Server Error', status=500)
        try:
            self.dc.devicecore._provision(['<device>whatever</device>'])
        except DeviceCloudHttpException:
            pass
        else:
            assert False, "should have thrown exception"

    def test_one_good(self):
        correct_response = [{'location': 'DeviceCore/123474/0', 'error': False}]
        self.prepare_response('POST', '/ws/DeviceCore', build_response(correct_response), status=SUCCESS_STATUS)
        result = self.dc.devicecore._provision(['<device>whatever</device>'])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], correct_response[0])

    def test_one_error(self):
        correct_response = [{'error': 'The device is already provisioned.', 'location': None}]
        self.prepare_response('POST', '/ws/DeviceCore', build_response(correct_response), status=ERRORS_STATUS)
        result = self.dc.devicecore._provision(['<device>whatever</device>'])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], correct_response[0])

    def test_two_good(self):
        correct_response = [{'location': 'DeviceCore/123474/0', 'error': False},
                            {'location': 'DeviceCore/123475/0', 'error': False}]
        self.prepare_response('POST', '/ws/DeviceCore', build_response(correct_response), status=SUCCESS_STATUS)
        result = self.dc.devicecore._provision(['<device>whatever</device>'] * 2)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        for i in range(len(result)):
            self.assertDictEqual(result[i], correct_response[i])

    def test_two_error(self):
        correct_response = [{'location': None, 'error': 'Problem with Device ID: Problem with segment number 4'},
                            {'location': None, 'error': 'The device is already provisioned.'}]
        self.prepare_response('POST', '/ws/DeviceCore', build_response(correct_response), status=ERRORS_STATUS)
        result = self.dc.devicecore._provision(['<device>whatever</device>'] * 2)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        for i in range(len(result)):
            self.assertDictEqual(result[i], correct_response[i])

    def test_two_split(self):
        correct_response = [{'location': 'DeviceCore/123474/0', 'error': False},
                            {'location': None, 'error': 'The device is already provisioned.'}]
        self.prepare_response('POST', '/ws/DeviceCore', build_response(correct_response), status=ERRORS_STATUS)
        result = self.dc.devicecore._provision(['<device>whatever</device>'] * 2)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        for i in range(len(result)):
            self.assertDictEqual(result[i], correct_response[i])


provision = mock.MagicMock()
provision.post.return_value.status_code = 201
provision.post.return_value.content = '<list></list>'


class ProvisionByTests(object):
    def setUp(self):
        HttpTestBase.setUp(self)
        global provision
        provision.reset_mock()

    def test_single(self):
        correct_response = {'location': 'DeviceCore/123474/0', 'error': False}
        self.prepare_response('POST', '/ws/DeviceCore', build_response(correct_response), status=SUCCESS_STATUS)
        result = self.provision_call('00:40:9d:aa:bb:cc')
        self.assertDictEqual(result, correct_response)

    def test_single_list(self):
        correct_response = [{'location': 'DeviceCore/123474/0', 'error': False}]
        self.prepare_response('POST', '/ws/DeviceCore', build_response(correct_response), status=SUCCESS_STATUS)
        result = self.provision_call(['00:40:9d:aa:bb:cc'])
        self.assertIsInstance(result, list)
        self.assertDictEqual(result[0], correct_response[0])

    @mock.patch.object(DeviceCoreAPI, '_provision', provision)
    def test_single_xml(self):
        self.provision_call('00:40:9d:aa:bb:cc')
        provision.assert_called_once_with(['<DeviceCore><{0}>00:40:9d:aa:bb:cc</{0}></DeviceCore>'.format(self.call_tag)])

    @mock.patch.object(DeviceCoreAPI, '_provision', provision)
    def test_single_list_xml(self):
        self.provision_call(['00:40:9d:aa:bb:cc'])
        provision.assert_called_once_with(['<DeviceCore><{0}>00:40:9d:aa:bb:cc</{0}></DeviceCore>'.format(self.call_tag)])

    @mock.patch.object(DeviceCoreAPI, '_provision', provision)
    def test_multi_list_xml(self):
        self.provision_call(['00:40:9d:aa:bb:cc', '00:40:9d:aa:bb:cd'])
        provision.assert_called_once_with(['<DeviceCore><{0}>00:40:9d:aa:bb:cc</{0}></DeviceCore>'.format(self.call_tag),
                                           '<DeviceCore><{0}>00:40:9d:aa:bb:cd</{0}></DeviceCore>'.format(self.call_tag)])


class ProvisionByIdTests(ProvisionByTests, HttpTestBase):
    def setUp(self):
        HttpTestBase.setUp(self)
        ProvisionByTests.setUp(self)
        self.provision_call = self.dc.devicecore.provision_by_id
        self.call_tag = "devConnectwareId"


class ProvisionByMacTests(ProvisionByTests, HttpTestBase):
    def setUp(self):
        HttpTestBase.setUp(self)
        ProvisionByTests.setUp(self)
        self.provision_call = self.dc.devicecore.provision_by_mac
        self.call_tag = "devMac"


if __name__ == '__main__':
    unittest.main()
