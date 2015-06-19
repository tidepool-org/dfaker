import unittest
import tools

class IOB_Tests(unittest.TestCase):
    
    def test_format_normal(self):
        self.input = [ {"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 3.5,
            "subType": "normal",
            "time": "2015-03-03T22:33:08.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"},
            { "deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:20:00",
            "id": "de34ecc6-841a-4e72-9f59-c3bcfb708feb",
            "normal": 5.31,
            "subType": "normal",
            "time": "2015-03-06T18:53:29.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = [[1425369600, 3.5], [1425370800, 5.31]]
        self.assertEqual(self.expected_output, tools.format_bolus_for_wizard(self.input))

    def test_format_sqaure(self):
        self.input = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "duration": 600000,
            "extended": 2.8,
            "id": "cdad40ee-9ec4-44bb-a466-afd1bf53e362",
            "subType": "square",
            "time": "2015-03-05T05:03:22.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = [[1425369600, 1.4],[1425369900, 1.4]]
        self.assertEqual(self.expected_output, tools.format_bolus_for_wizard(self.input))
    
    def test_format_dual_square(self):
        self.input = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "duration": 600000,
            "extended": 3.0,
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 4.0,
            "subType": "dual/square",
            "time": "2015-03-03T22:33:08.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = [[1425369600, 4.0], [1425369600, 1.5],  [1425369900, 1.5]]
        self.assertEqual(self.expected_output, tools.format_bolus_for_wizard(self.input))

    def test_simple_iob_dict_creation(self):
        self.input = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 6,
            "subType": "normal",
            "time": "2015-03-03T22:33:08.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = {1425369600: 6.0, 1425369900:5.5, 1425370200: 5.0, 
                                1425370500: 4.5, 1425370800: 4.0, 1425371100: 3.5,
                                1425371400: 3.0, 1425371700: 2.5, 1425372000: 2.0,
                                1425372300: 1.5, 1425372600: 1.0, 1425372900: 0.5}
        self.assertEqual(self.expected_output, tools.creare_iob_dict(self.input, action_time=1))

    def test_complex_iob_dict_creation(self):
        self.input = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 10,
            "subType": "normal",
            "time": "2015-03-03T22:33:08.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"},
            {"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:05:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 10,
            "subType": "normal",
            "time": "2015-03-03T22:33:08.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = {1425369600: 10.0,  1425369900: 15, 1425370200: 5}
        self.assertEqual(self.expected_output, tools.creare_iob_dict(self.input, action_time=10/60))

    def test_iob_update(self):
        self.curr_dict = {1425369600: 10.0,  1425369900: 15, 1425370200: 5}
        self.associated_bolus = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:10:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 10,
            "subType": "normal",
            "time": "2015-03-03T22:33:08.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = {1425369600: 10.0,  1425369900: 15.0, 1425370200: 15.0, 1425370500: 5.0}
        (self.assertEqual(self.expected_output, 
            tools.update_iob_bolus_dict(self.curr_dict, self.associated_bolus, action_time=10/60)))        

    def test_insulin_on_board(self):
        self.curr_dict =  {1425369600: 10.0,  1425369900: 15.0, 1425370200: 15.0, 1425370500: 5.0}
        self.exact_timestamp =  1425369900
        self.expected_exact_output = 15.0
        self.approx_timestamp = 1425370600
        self.expected_approx_output = 5.0
        self.far_timestamp = 1425370801
        self.expected_far_output = 0
        self.test_boundry_timestamp = 1425369300
        self.expected_boundry_output = 10.0

        self.assertEqual(self.expected_exact_output, tools.insulin_on_board(self.curr_dict, self.exact_timestamp))
        self.assertEqual(self.expected_approx_output, tools.insulin_on_board(self.curr_dict, self.approx_timestamp))
        self.assertEqual(self.expected_far_output, tools.insulin_on_board(self.curr_dict, self.far_timestamp))
        self.assertEqual(self.expected_boundry_output, tools.insulin_on_board(self.curr_dict, self.test_boundry_timestamp))

if __name__ == '__main__':
    unittest.main()











