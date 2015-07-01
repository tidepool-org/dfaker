from chai import Chai
import unittest
from datetime import datetime

import dfaker.wizard as wizard
import dfaker.tools as tools

class Test_Wizard(Chai):

    def test_wizard_format_no_iob(self):
        """ Test that wizard events meet format requirements"""
        start_time = datetime(2015, 1, 1, 0, 0 ,0)
        #populate gluc list with some fake glucose values
        gluc = [100, 217, 49]
        #populate carb list with some fake carb values (corresponding to a meal)
        carbs = [90, 31, 61]
        #populate timesteps with some fake time values later than start_time
        timesteps = [tools.convert_ISO_to_epoch('2015-01-01 15:00:00', '%Y-%m-%d %H:%M:%S'),
                    tools.convert_ISO_to_epoch('2015-01-02 19:30:00', '%Y-%m-%d %H:%M:%S'),
                    tools.convert_ISO_to_epoch('2015-01-03 09:12:00', '%Y-%m-%d %H:%M:%S')]
        #test that wizard events formats correctly even when no bolus and no_wizard data is given
        bolus_data = []
        no_wizard = []
        zonename = 'US/Pacific'
        res_dict = wizard.wizard(start_time, gluc, carbs, timesteps, bolus_data, no_wizard, zonename) 
        #make sure that for every wizrd event, a bolus event is also created (ie there shold be 6 total events)
        self.assertEqual(len(res_dict), 6)

        #check that the reccomendation of the wizard calculates correctly
        carb_ratio1 = res_dict[1]["insulinCarbRatio"] 
        carb_input1 = res_dict[1]["carbInput"] #should match carbs[0] = 90
        net_reccomendation1 = res_dict[1]["recommended"]["net"]
        expected_reccomendation1 = tools.round_to(carb_input1 / carb_ratio1)
        self.assertEqual(net_reccomendation1, expected_reccomendation1)

        carb_ratio2 = res_dict[3]["insulinCarbRatio"] 
        carb_input2 = res_dict[3]["carbInput"] #should match carbs[0] = 90
        net_reccomendation2 = res_dict[3]["recommended"]["net"]
       
        expected_reccomendation2 = tools.round_to(carb_input2 / carb_ratio2)
        self.assertEqual(net_reccomendation2, expected_reccomendation2)

        carb_ratio3 = res_dict[5]["insulinCarbRatio"] 
        carb_input3 = res_dict[5]["carbInput"] #should match carbs[0] = 90
        net_reccomendation3 = res_dict[5]["recommended"]["net"]
        expected_reccomendation3 = tools.round_to(carb_input3 / carb_ratio3)
        self.assertEqual(net_reccomendation3, expected_reccomendation3)

    def test_wizard_format_with_iob(self):
        """ Test insulin on board calculations are taken into account when giving a wizard reccomendation"""
        start_time = datetime(2015, 1, 1, 0, 0 ,0)
        gluc = [100]
        carbs = [90]
        timesteps = [tools.convert_ISO_to_epoch('2015-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')]
        bolus_data = [{ "deviceId": "DemoData-123456789", 
                        "deviceTime": "2015-01-01T07:59:29",
                        "id": "3db26422-e731-429e-ab14-7dfc78a399f3",
                        "normal": 10, #iob value should correspond to this value!
                        "subType": "normal",
                        "time": "2015-01-01T00:00:00.000Z", #same time as wizard
                        "timezoneOffset": -480.0,
                        "type": "bolus",
                        "uploadId": "upid_abcdefghijklmnop"}]
        no_wizard = []
        zonename = 'US/Pacific'
        res_dict = wizard.wizard(start_time, gluc, carbs, timesteps, bolus_data, no_wizard, zonename) 
        
        #check that insulin on board value is correct
        expected_iob = tools.convert_to_mmol(10)
        iob = res_dict[1]["insulinOnBoard"]
        self.assertEqual(expected_iob, iob)

        #check that net reccomendationt takes into account insulin on board 
        carb_ratio = res_dict[1]["insulinCarbRatio"] 
        carb_input = res_dict[1]["carbInput"] #should match carbs[0] = 90
        net_reccomendation = res_dict[1]["recommended"]["net"]
        expected_reccomendation = tools.round_to(carb_input / carb_ratio) - tools.round_to(iob)

        self.assertEqual(net_reccomendation, expected_reccomendation)

    def test_insulin_sensitivity(self):
        """ Test that insulin sensitivity is assigned correctly according to time of day"""
        start_time = datetime(2015, 1, 1, 0, 0 ,0)
        #gluc and carb values do not affect sensistivity
        gluc = [100, 100, 100, 100]
        carbs = [100, 100, 100, 100]
        timesteps = [tools.convert_ISO_to_epoch('2015-01-01 04:30:00', '%Y-%m-%d %H:%M:%S'),
                    tools.convert_ISO_to_epoch('2015-01-01 10:45:00', '%Y-%m-%d %H:%M:%S'),
                    tools.convert_ISO_to_epoch('2015-01-01 13:12:00', '%Y-%m-%d %H:%M:%S'),
                    tools.convert_ISO_to_epoch('2015-01-01 23:56:00', '%Y-%m-%d %H:%M:%S')]
        bolus_data = []
        no_wizard = []
        #zonemae here is in UTC so that timestems reflect time and deviceTime to make time checking easier 
        zonename = 'UTC'
        res_dict = wizard.wizard(start_time, gluc, carbs, timesteps, bolus_data, no_wizard, zonename)

        #expected sensitivity:
        expected_early_morning = tools.convert_to_mmol(30)
        expected_morning = tools.convert_to_mmol(40)
        expected_afternoon = tools.convert_to_mmol(50)
        expected_night = tools.convert_to_mmol(35)

        #resulting sensitivity:
        early_morning = res_dict[1]["insulinSensitivity"]
        morning = res_dict[3]["insulinSensitivity"]
        afternoon = res_dict[5]["insulinSensitivity"]
        night = res_dict[7]["insulinSensitivity"]

        self.assertEqual(expected_early_morning, early_morning)
        self.assertEqual(expected_morning, morning)
        self.assertEqual(expected_afternoon, afternoon)
        self.assertEqual(expected_night, night)

    def test_no_wizard(self):
        """ Test that wizard and associated bolus events are removed during no_wizard periods"""
        start_time = datetime(2015, 1, 1, 0, 0 ,0)
        gluc = [87, 201, 164, 180]
        carbs = [96, 82, 17, 53]
        timesteps = [tools.convert_ISO_to_epoch('2015-01-01 04:00:00', '%Y-%m-%d %H:%M:%S'),
                     tools.convert_ISO_to_epoch('2015-01-01 05:00:00', '%Y-%m-%d %H:%M:%S'),
                     tools.convert_ISO_to_epoch('2015-01-01 06:00:00', '%Y-%m-%d %H:%M:%S'),
                     tools.convert_ISO_to_epoch('2015-01-01 07:00:00', '%Y-%m-%d %H:%M:%S')]
        bolus_data = []
        #create two time ranges during which there should not be bolus events
        no_wizard_start1 = tools.convert_ISO_to_epoch('2015-01-01 04:55:00', '%Y-%m-%d %H:%M:%S')
        no_wizard1_end1 = tools.convert_ISO_to_epoch('2015-01-01 05:05:00', '%Y-%m-%d %H:%M:%S')
        no_wizard_start2 = tools.convert_ISO_to_epoch('2015-01-01 06:55:00', '%Y-%m-%d %H:%M:%S')
        no_wizard1_end2 = tools.convert_ISO_to_epoch('2015-01-01 07:05:00', '%Y-%m-%d %H:%M:%S')
        no_wizard = [[no_wizard_start1, no_wizard1_end1], 
                     [no_wizard_start2, no_wizard1_end2]]
        zonename = 'US/Pacific'
        res_dict = wizard.wizard(start_time, gluc, carbs, timesteps, bolus_data, no_wizard, zonename) 

        #after no_wizard events are removed, 2 wizard events + 2 bolus events should remain
        self.assertEqual(len(res_dict), 4)
 
def suite():
    """ Gather all the tests from this module in a test suite """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(Test_Wizard))
    return test_suite

mySuit = suite()

runner = unittest.TextTestRunner()
runner.run(mySuit)

