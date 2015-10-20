from chai import Chai
import unittest

import dfaker.common_fields as common_fields
import dfaker.tools as tools

class Test_Common_Fields(Chai):

    def test_common_fields(self):
        """ Test that common fields populate properly"""
        name = "bolus"
        datatype = {}
        timestamp = tools.convert_ISO_to_epoch('2015-03-03 00:00:00', '%Y-%m-%d %H:%M:%S')
        zonename = "US/Pacific"

        expected = {
            'time': '2015-03-03T00:00:00.000Z', #UTC time
            'deviceTime': '2015-03-02T16:00:00', #local time
            'timezoneOffset': -480,
            'deviceId': 'DemoData-123456789',
            'uploadId': 'upid_abcdefghijklmnop',
            'conversionOffset': 0,
        }

        result_dict = common_fields.add_common_fields(name, datatype, timestamp, zonename)

        for key in expected.keys():
            self.assertEqual(result_dict[key], expected[key])


def suite():
    """ Gather all the tests from this module in a test suite """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(Test_Common_Fields))
    return test_suite

mySuit = suite()

runner = unittest.TextTestRunner()
runner.run(mySuit)

