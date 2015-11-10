from chai import Chai
import unittest
from datetime import datetime

import dfaker.basal as basal
import dfaker.tools as tools


class Test_Basal(Chai):

    def test_basal_schedule(self):
        """ Test that basal rates are assinged according to the basal schedule
            from settings"""
        start_time = datetime(2015, 1, 1, 0, 0, 0)
        num_days = 1
        zonename = 'US/Pacific'
        pump_name = 'Medtronic'
        res_dict, suspend_pump = basal.scheduled_basal(start_time, num_days,
                                                       zonename, pump_name)

        # expected segments and rate (from settings)
        segment_one = range(tools.convert_ISO_to_epoch('2015-01-01 00:00:00',
                                                       '%Y-%m-%d %H:%M:%S'),
                            tools.convert_ISO_to_epoch('2015-01-01 01:00:00',
                                                       '%Y-%m-%d %H:%M:%S'))
        rate_one = 0.9
        segment_two = range(tools.convert_ISO_to_epoch('2015-01-01 01:00:00',
                                                       '%Y-%m-%d %H:%M:%S'),
                            tools.convert_ISO_to_epoch('2015-01-01 03:00:00',
                                                       '%Y-%m-%d %H:%M:%S'))
        rate_two = 0.6
        segment_three = range(tools.convert_ISO_to_epoch('2015-01-01 03:00:00',
                                                         '%Y-%m-%d %H:%M:%S'),
                              tools.convert_ISO_to_epoch('2015-01-01 04:00:00',
                                                         '%Y-%m-%d %H:%M:%S'))
        rate_three = 0.65
        segment_four = range(tools.convert_ISO_to_epoch('2015-01-01 04:00:00',
                                                        '%Y-%m-%d %H:%M:%S'),
                             tools.convert_ISO_to_epoch('2015-01-01 05:00:00',
                                                        '%Y-%m-%d %H:%M:%S'))
        rate_four = 0.8
        segment_five = range(tools.convert_ISO_to_epoch('2015-01-01 05:00:00',
                                                        '%Y-%m-%d %H:%M:%S'),
                             tools.convert_ISO_to_epoch('2015-01-01 08:00:00',
                                                        '%Y-%m-%d %H:%M:%S'))
        rate_five = 0.85
        segment_six = range(tools.convert_ISO_to_epoch('2015-01-01 08:00:00',
                                                       '%Y-%m-%d %H:%M:%S'),
                            tools.convert_ISO_to_epoch('2015-01-01 09:00:00',
                                                       '%Y-%m-%d %H:%M:%S'))
        rate_six = 0.8
        segment_seven = range(tools.convert_ISO_to_epoch('2015-01-01 09:00:00',
                                                         '%Y-%m-%d %H:%M:%S'),
                              tools.convert_ISO_to_epoch('2015-01-01 15:00:00',
                                                         '%Y-%m-%d %H:%M:%S'))
        rate_seven = 0.75
        segment_eight = range(tools.convert_ISO_to_epoch('2015-01-01 15:00:00',
                                                         '%Y-%m-%d %H:%M:%S'),
                              tools.convert_ISO_to_epoch('2015-01-01 17:00:00',
                                                         '%Y-%m-%d %H:%M:%S'))
        rate_eight = 0.8
        segment_nine = range(tools.convert_ISO_to_epoch('2015-01-01 17:00:00',
                                                        '%Y-%m-%d %H:%M:%S'),
                             tools.convert_ISO_to_epoch('2015-01-02 00:00:00',
                                                        '%Y-%m-%d %H:%M:%S'))
        rate_nine = 0.85

        # check that expected rates match results
        for entry in res_dict:
            if entry["type"] == "basal":
                if entry['deliveryType'] == 'scheduled':
                    entry_time = tools.convert_ISO_to_epoch(
                        entry["deviceTime"], '%Y-%m-%dT%H:%M:%S')
                    if entry_time in segment_one:
                        self.assertEqual(entry['rate'], rate_one)
                    elif entry_time in segment_two:
                        self.assertEqual(entry['rate'], rate_two)
                    elif entry_time in segment_three:
                        self.assertEqual(entry['rate'], rate_three)
                    elif entry_time in segment_four:
                        self.assertEqual(entry['rate'], rate_four)
                    elif entry_time in segment_five:
                        self.assertEqual(entry['rate'], rate_five)
                    elif entry_time in segment_six:
                        self.assertEqual(entry['rate'], rate_six)
                    elif entry_time in segment_seven:
                        self.assertEqual(entry['rate'], rate_seven)
                    elif entry_time in segment_eight:
                        self.assertEqual(entry['rate'], rate_eight)
                    elif entry_time in segment_nine:
                        self.assertEqual(entry['rate'], rate_nine)
                    else:
                        raise Exception("Invalid segment")


def suite():
    """ Gather all the tests from this module in a test suite """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(Test_Basal))
    return test_suite

mySuit = suite()

runner = unittest.TextTestRunner()
runner.run(mySuit)
