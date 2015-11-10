from chai import Chai
import unittest
import numpy as np

import dfaker.tools as tools
import dfaker.bolus as bolus


class Test_Bolus(Chai):

    def test_night_bolus_removal(self):
        """ Test that night boluses are removed properly"""
        # bolus removal depandent on time of day and glucose level
        # the function takes a list of carb-time-glucose lists and a timezone
        # name
        night_time = tools.convert_ISO_to_epoch('2015-01-01 00:30:00',
                                                '%Y-%m-%d %H:%M:%S')
        zonemane = "US/Pacific"
        offset = -480
        # removing night events must happen in the user's local time
        local_epoch_night_time = night_time - offset*60
        # remove
        test_in_range_night_event = [[90, local_epoch_night_time, 249]]
        # keep
        test_high_night_event = [[90, local_epoch_night_time, 250]]

        expected_removed_event = []
        expected_kept_event = [[90, local_epoch_night_time, 250]]

        # call to function returns a numpy list which is converted to a
        # regular list for these tests
        result_removed = bolus.remove_night_boluses(test_in_range_night_event,
                                                    zonemane)
        self.assertEqual(expected_removed_event,
                         np.ndarray.tolist(result_removed))

        result_kept = bolus.remove_night_boluses(test_high_night_event,
                                                 zonemane)
        self.assertEqual(expected_kept_event, np.ndarray.tolist(result_kept))


def suite():
    """ Gather all the tests from this module in a test suite """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(Test_Bolus))
    return test_suite

mySuit = suite()

runner = unittest.TextTestRunner()
runner.run(mySuit)
