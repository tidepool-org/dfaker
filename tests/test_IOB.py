from chai import Chai
import unittest

import dfaker.insulin_on_board as insulin_on_board
import dfaker.tools as tools


class Test_IOB(Chai):

    def test_simple_iob_dict_creation(self):
        """ Check a single insulin dose distribution over action_time = one
            hour"""
        expected_input = [
            {
                "deviceId": "DemoData-123456789",
                "deviceTime": "2015-03-03T00:00:00",
                "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
                "normal": 6,
                "subType": "normal",
                "time": "2015-03-03T00:00:00.000Z",
                "timezoneOffset": -480.0,
                "type": "bolus",
                "uploadId": "upid_abcdefghijklmnop"
            }
        ]
        res_dict = insulin_on_board.create_iob_dict(expected_input,
                                                    action_time=1)
        half_way_key = tools.convert_ISO_to_epoch('2015-03-03T00:30:00.000Z',
                                                  '%Y-%m-%dT%H:%M:%S.000Z')
        half_way = res_dict[half_way_key]  # 30 mins later
        three_fourth_key = tools.convert_ISO_to_epoch(
            '2015-03-03T00:45:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        three_fourth = res_dict[three_fourth_key]  # 45 mins later
        # test that halfway through the action time, IOB is half the original
        # bolus
        self.assertEqual(tools.round_to(half_way),
                         float(expected_input[0]['normal'] / 2))
        # test that 75% through the action time, IOB is one fourth the original
        # bolus
        self.assertEqual(tools.round_to(three_fourth),
                         float(expected_input[0]['normal'] / 4))

    def test_complex_iob_dict_creation(self):
        """ Check two insulin doses five minutes apart, action_time = 10
            minutes"""
        expected_input = [
            {
                "deviceId": "DemoData-123456789",
                "deviceTime": "2015-03-03T00:00:00",
                "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
                "normal": 10,
                "subType": "normal",
                "time": "2015-03-03T00:00:00.000Z",
                "timezoneOffset": -480.0,
                "type": "bolus",
                "uploadId": "upid_abcdefghijklmnop"
            },
            {
                "deviceId": "DemoData-123456789",
                "deviceTime": "2015-03-03T00:05:00",
                "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
                "normal": 10,
                "subType": "normal",
                "time": "2015-03-03T00:05:00.000Z",
                "timezoneOffset": -480.0,
                "type": "bolus",
                "uploadId": "upid_abcdefghijklmnop"
            }
        ]
        res_dict = insulin_on_board.create_iob_dict(expected_input,
                                                    action_time=10/60)
        initial_iob_key = tools.convert_ISO_to_epoch(
            '2015-03-03T00:00:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        initial_iob = res_dict[initial_iob_key]
        five_min_key = tools.convert_ISO_to_epoch(
            '2015-03-03T00:05:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        five_min = res_dict[five_min_key]
        ten_min_key = tools.convert_ISO_to_epoch(
            '2015-03-03T00:10:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        ten_min = res_dict[ten_min_key]

        # At time = 0 min, IOB should be 10
        self.assertEqual(initial_iob, 10.0)
        # At time = 5 min, initial IOB = 5 + second IOB = 10 --> 15 total
        self.assertEqual(five_min, 15.0)
        # At time = 10 min, initial IOB = 0, and second IOB should have 5 units
        # left
        self.assertEqual(ten_min, 5.0)

    def test_iob_update(self):
        """ Test updating an existing dictionary with a new bolus entry"""
        # IOB values 5 minutes apart for 10 minutes
        curr_dict = {1425340800: 10.0,  1425341100: 15, 1425341400: 5}
        associated_bolus = [
            {
                "deviceId": "DemoData-123456789",
                "deviceTime": "2015-03-03T00:10:00",
                "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
                "normal": 10,
                "subType": "normal",
                "time": "2015-03-03T00:10:00.000Z",
                "timezoneOffset": -480.0,
                "type": "bolus",
                "uploadId": "upid_abcdefghijklmnop"
            }
        ]

        res_dict = insulin_on_board.update_iob_dict(curr_dict,
                                                    associated_bolus,
                                                    action_time=10/60)
        initial_iob_key = tools.convert_ISO_to_epoch(
            '2015-03-03T00:00:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        initial_iob = res_dict[initial_iob_key]
        five_min_key = tools.convert_ISO_to_epoch('2015-03-03T00:05:00.000Z',
                                                  '%Y-%m-%dT%H:%M:%S.000Z')
        five_min = res_dict[five_min_key]
        ten_min_key = tools.convert_ISO_to_epoch('2015-03-03T00:10:00.000Z',
                                                 '%Y-%m-%dT%H:%M:%S.000Z')
        ten_min = res_dict[ten_min_key]
        fifteen_min_key = tools.convert_ISO_to_epoch(
            '2015-03-03T00:15:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        fifteen_min = res_dict[fifteen_min_key]

        # At time = 0 min, IOB should be 10, (same as original dict)
        self.assertEqual(initial_iob, 10.0)
        # At time = 5 min, IOB should be 15, (same as original dict)
        self.assertEqual(five_min, 15.0)
        # At time = 10 min, the original dict value of 5 should add to the new
        # bolus of 10 --> 15 total
        self.assertEqual(ten_min, 15.0)
        # At time = 15 min, the original dict should update to account for the
        # 5 remaining units of the new entry
        self.assertEqual(fifteen_min, 5.0)

    def test_insulin_on_board(self):
        """ Check that assigning iob values to specific times works as
            intended """
        start_time = tools.convert_ISO_to_epoch('2015-03-03T00:00:00.000Z',
                                                '%Y-%m-%dT%H:%M:%S.000Z')
        five_min = tools.convert_ISO_to_epoch('2015-03-03T00:05:00.000Z',
                                              '%Y-%m-%dT%H:%M:%S.000Z')
        ten_min = tools.convert_ISO_to_epoch('2015-03-03T00:10:00.000Z',
                                             '%Y-%m-%dT%H:%M:%S.000Z')
        fifteen_min = tools.convert_ISO_to_epoch('2015-03-03T00:15:00.000Z',
                                                 '%Y-%m-%dT%H:%M:%S.000Z')
        curr_dict = {start_time: 10.0,  five_min: 15.0, ten_min: 15.0,
                     fifteen_min: 5.0}

        # test an iob value for a time that exists in the dict
        exact_time = start_time
        expected_exact_output = 10.0
        self.assertEqual(expected_exact_output,
                         insulin_on_board.insulin_on_board(curr_dict,
                                                           exact_time))

        # test iob values within 5 minutes of a time value that exists in the
        # dict
        approx_time_round_down = tools.convert_ISO_to_epoch(
            # 4 mins away from fifteen_min
            '2015-03-03T00:19:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        approx_time_round_up = tools.convert_ISO_to_epoch(
            # 1 min away from fifteen_min
            '2015-03-03T00:14:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        expected_approx_output = 5.0
        self.assertEqual(
            expected_approx_output,
            insulin_on_board.insulin_on_board(curr_dict,
                                              approx_time_round_down))
        self.assertEqual(
            expected_approx_output,
            insulin_on_board.insulin_on_board(curr_dict, approx_time_round_up))

        # test an iob value that is out of the 5 minute approximation range
        far_time = tools.convert_ISO_to_epoch('2015-03-03T00:22:00.000Z',
                                              '%Y-%m-%dT%H:%M:%S.000Z')
        expected_far_output = 0
        self.assertEqual(
            expected_far_output,
            insulin_on_board.insulin_on_board(curr_dict, far_time))

        # test the boundy case of exactly 5 minutes away from fifteen_min
        boundry_time = tools.convert_ISO_to_epoch('2015-03-03T00:20:00.000Z',
                                                  '%Y-%m-%dT%H:%M:%S.000Z')
        expected_boundry_output = 5.0
        self.assertEqual(
            expected_boundry_output,
            insulin_on_board.insulin_on_board(curr_dict, boundry_time))


def suite():
    """ Gather all the tests from this module in a test suite """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(Test_IOB))
    return test_suite

mySuit = suite()

runner = unittest.TextTestRunner()
runner.run(mySuit)
