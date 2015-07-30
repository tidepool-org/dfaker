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

        #expected_format:
        time = '2015-03-03T00:00:00.000Z' #UTC time
        deviceTime = '2015-03-02T16:00:00' #local time
        timezoneOffset = -480
        deviceId = 'DemoData-123456789'
        uploadId = 'upid_abcdefghijklmnop'

        result_dict = common_fields.add_common_fields(name, datatype, timestamp, zonename)
        for key in result_dict:
            if key == 'time':
                self.assertEqual(result_dict[key], time)
            elif key == 'deviceTime':
                self.assertEqual(result_dict[key], deviceTime)
            elif key == 'timezoneOffset':
                self.assertEqual(result_dict[key], timezoneOffset)
            elif key == 'deviceId':
                self.assertEqual(result_dict[key], deviceId)
            elif key == 'uploadId':
                self.assertEqual(result_dict[key], uploadId)


def suite():
    """ Gather all the tests from this module in a test suite """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(Test_Common_Fields))
    return test_suite

mySuit = suite()

runner = unittest.TextTestRunner()
runner.run(mySuit)

