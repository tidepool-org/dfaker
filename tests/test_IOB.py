import unittest
import insulin_on_board

class IOB_Tests(unittest.TestCase):
    
    def test_format_normal(self):
        self.input = [ {"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 3.5,
            "subType": "normal",
            "time": "2015-03-03T00:00:00.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"},
            { "deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:20:00",
            "id": "de34ecc6-841a-4e72-9f59-c3bcfb708feb",
            "normal": 5.31,
            "subType": "normal",
            "time": "2015-03-03T00:20:00.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = [[1425340800, 3.5], [1425342000, 5.31]]
        self.assertEqual(self.expected_output, insulin_on_board.format_bolus_for_wizard(self.input))
   
    def test_format_sqaure(self):
        self.input = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "duration": 600000,
            "extended": 2.8,
            "id": "cdad40ee-9ec4-44bb-a466-afd1bf53e362",
            "subType": "square",
            "time": "2015-03-03T00:00:00.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = [[1425340800, 1.4],[1425341100, 1.4]]
        self.assertEqual(self.expected_output, insulin_on_board.format_bolus_for_wizard(self.input))
    
    def test_format_dual_square(self):
        self.input = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "duration": 600000,
            "extended": 3.0,
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 4.0,
            "subType": "dual/square",
            "time": "2015-03-03T00:00:00.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = [[1425340800, 4.0], [1425340800, 1.5],  [1425341100, 1.5]]
        self.assertEqual(self.expected_output, insulin_on_board.format_bolus_for_wizard(self.input))

    def test_simple_iob_dict_creation(self):
        self.input = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 6,
            "subType": "normal",
            "time": "2015-03-03T00:00:00.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = {1425340800: 6.0, 1425341100: 5.5, 1425341400: 5.0, 
                                1425341700: 4.5, 1425342000: 4.0, 1425342300: 3.5,
                                1425342600: 3.0, 1425342900: 2.5, 1425343200: 2.0,
                                1425343500: 1.5, 1425343800: 1.0, 1425344100: 0.5}
        self.assertEqual(self.expected_output, insulin_on_board.creare_iob_dict(self.input, action_time=1))

    def test_complex_iob_dict_creation(self):
        self.input = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:00:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 10,
            "subType": "normal",
            "time": "2015-03-03T00:00:00.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"},
            {"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:05:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 10,
            "subType": "normal",
            "time": "2015-03-03T00:05:00.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = {1425340800: 10.0,  1425341100: 15, 1425341400: 5}
        self.assertEqual(self.expected_output, insulin_on_board.creare_iob_dict(self.input, action_time=10/60))

    def test_iob_update(self):
        self.curr_dict = {1425340800: 10.0,  1425341100: 15, 1425341400: 5}
        self.associated_bolus = [{"deviceId": "DemoData-123456789",
            "deviceTime": "2015-03-03T00:10:00",
            "id": "002650eb-3d53-4a3d-b39f-6cd0c1ce58f2",
            "normal": 10,
            "subType": "normal",
            "time": "2015-03-03T00:10:00.000Z",
            "timezoneOffset": -480.0,
            "type": "bolus",
            "uploadId": "upid_abcdefghijklmnop"}]
        self.expected_output = {1425340800: 10.0,  1425341100: 15.0, 1425341400: 15.0, 1425341700: 5.0}
        (self.assertEqual(self.expected_output, 
            insulin_on_board.update_iob_dict(self.curr_dict, self.associated_bolus, action_time=10/60)))        

    def test_insulin_on_board(self):
        self.curr_dict =  {1425369600: 10.0,  1425369900: 15.0, 1425370200: 15.0, 1425370500: 5.0}
        self.exact_timestamp =  1425369900
        self.expected_exact_output = 15.0
        self.approx_timestamp = 1425370600
        self.expected_approx_output = 5.0
        self.far_timestamp = 1425370801
        self.expected_far_output = 0
        self.boundry_timestamp = 1425369300
        self.expected_boundry_output = 10.0

        self.assertEqual(self.expected_exact_output, insulin_on_board.insulin_on_board(self.curr_dict, self.exact_timestamp))
        self.assertEqual(self.expected_approx_output, insulin_on_board.insulin_on_board(self.curr_dict, self.approx_timestamp))
        self.assertEqual(self.expected_far_output, insulin_on_board.insulin_on_board(self.curr_dict, self.far_timestamp))
        self.assertEqual(self.expected_boundry_output, insulin_on_board.insulin_on_board(self.curr_dict, self.boundry_timestamp))

if __name__ == '__main__':
    unittest.main()
