from chai import Chai
import unittest
from datetime import datetime

import dfaker.tools as tools


class Test_Tools(Chai):

    def test_spring_forward_offset(self):
        """ Test edge cases around the spring forward time change """
        pacific_zone = 'US/Pacific'
        no_dst_date = datetime(2015, 3, 8, 1, 59, 0)  # 03/08/2015 1:59 AM
        dst_date = datetime(2015, 3, 8, 3, 0, 0)  # 03/08/2015 3:00 AM
        expected_pacific_dst_offset = -420
        expected_pacific_no_dst_offset = -480
        self.assertEqual(expected_pacific_dst_offset,
                         tools.get_offset(pacific_zone, dst_date))
        self.assertEqual(expected_pacific_no_dst_offset,
                         tools.get_offset(pacific_zone, no_dst_date))

    def test_fall_back_offset(self):
        """ Test edge cases around the fall back time change """
        pacific_zone = 'US/Pacific'
        dst_date = datetime(2015, 11, 1, 0, 59, 0)  # 11/01/2015 12:59 AM
        no_dst_date = datetime(2015, 11, 1, 2, 0, 0)  # 11/01/2015 2:00 AM
        expected_dst_offset = -420
        expected_no_dst_offset = -480
        self.assertEqual(expected_dst_offset,
                         tools.get_offset(pacific_zone, dst_date))
        self.assertEqual(expected_no_dst_offset,
                         tools.get_offset(pacific_zone, no_dst_date))

    def test_NZ_offset(self):
        """ Test offset in New Zealand (+12:00 hours no DST)"""
        nz_zone = 'NZ'
        no_dst_date = datetime(2015, 6, 25)
        expected_offset = 720
        self.assertEqual(expected_offset,
                         tools.get_offset(nz_zone, no_dst_date))

    def test_mmol_conversion(self):
        """ Test conversion from mg/dL to mmol for an iterable and for
            individual floats or integers"""
        input_list = [180, 150, 110, 80, 50]
        expected_output_list = [9.991346383881961, 8.3261219865683,
                                6.1058227901500866, 4.440598392836427,
                                2.7753739955227665]
        input_float = 97.892
        expected_float = 5.433738223394293
        input_int = 97
        expected_int = 5.3842255513141675

        self.assertEqual(expected_output_list,
                         tools.convert_to_mmol(input_list))
        self.assertEqual(expected_float, tools.convert_to_mmol(input_float))
        self.assertEqual(expected_int, tools.convert_to_mmol(input_int))

    def test_float_rounding(self):
        """ Test rounding floats to specified percision """
        # Note, the round_to function always trunctuates the result to three
        # decimal points
        positive_float = 6.124849333
        negative_float = -7.89209123
        low_precision = 0.5
        medium_precision = 0.05
        high_precision = 0.0005

        # expected results for each percision:
        lp_positive, lp_negative = 6.0, -8.0
        md_positive, md_negative = 6.10, -7.90
        hp_positive, hp_negative = 6.125, -7.892

        self.assertEqual(lp_positive,
                         tools.round_to(positive_float, low_precision))
        self.assertEqual(lp_negative,
                         tools.round_to(negative_float, low_precision))

        self.assertEqual(md_positive,
                         tools.round_to(positive_float, medium_precision))
        self.assertEqual(md_negative,
                         tools.round_to(negative_float, medium_precision))

        self.assertEqual(hp_positive,
                         tools.round_to(positive_float, high_precision))
        self.assertEqual(hp_negative,
                         tools.round_to(negative_float, high_precision))

    def test_timestep_creation(self):
        """ Based on a start time and a list of incrementing numbers, test
            generation of epoch timesteps"""
        start_time = datetime(2015, 1, 1, 0, 0, 0)  # 01/01/2015 00:00
        offset = -480
        time_list_every_5min = [0, 5, 10]
        # generated using http://www.epochconverter.com/
        expected_5min_output = [1420099200, 1420099500, 1420099800]

        time_list_every_hour = [0, 60, 120]
        # generated using http://www.epochconverter.com/
        expected_hourly_output = [1420099200, 1420102800, 1420106400]

        self.assertEqual(
            expected_5min_output,
            tools.make_timesteps(start_time, offset, time_list_every_5min))
        self.assertEqual(
            expected_hourly_output,
            tools.make_timesteps(start_time, offset, time_list_every_hour))


def suite():
    """ Gather all the tests from this module in a test suite """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(Test_Tools))
    return test_suite

mySuit = suite()

runner = unittest.TextTestRunner()
runner.run(mySuit)
