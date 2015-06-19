import random
import settings
import common_fields
import tools
from bolus import square_bolus, normal_bolus, dual_square_bolus, check_bolus_time

def wizard(start_time, gluc, carbs, timesteps, basal_data, bolus_data, no_wizard, zonename):
    """ Construct a wizard event
        start_time -- a datetime object with a timezone
        gluc -- a list of glucose values at each timestep 
        carbs -- a list of carb events at each timestep
        timesteps -- a list of epoch times 
        basal_data -- of list of basal data dictionaries to calculate IOB
        no_wizard -- a list of lists of start and end times during which there should be no bolus events
                    for example, when the pump was suspended 
        zonename -- name of timezone in effect 
    """
    wizard_data = []
    access_settings = settings.settings(start_time, zonename)[0]

    iob_dict = tools.creare_iob_dict(bolus_data, access_settings["actionTime"])

    for gluc_val, carb_val, timestamp in zip(gluc, carbs, timesteps):
        if check_bolus_time(timestamp, no_wizard):    
            wizard_reading = {}
            wizard_reading = common_fields.add_common_fields('wizard', wizard_reading, timestamp, zonename)
            wizard_reading["bgInput"] = tools.convert_to_mmol(gluc_val)
            wizard_reading["carbInput"] = int(carb_val)
            iob = tools.insulin_on_board(iob_dict, int(timestamp))
            wizard_reading["insulinOnBoard"] = tools.convert_to_mmol(iob)  
            carb_ratio_sched, sensitivity_sched = access_settings["carbRatio"], access_settings["insulinSensitivity"]
            sensitivity = tools.get_rate_from_settings(sensitivity_sched, wizard_reading["deviceTime"], "insulinSensitivity")
            carb_ratio = tools.get_rate_from_settings(carb_ratio_sched, wizard_reading["deviceTime"], "carbRatio")
            wizard_reading["insulinSensitivity"] = sensitivity
            wizard_reading["insulinCarbRatio"] = carb_ratio
            wizard_reading["bgTarget"] = { "high": access_settings["bgTarget"][0]["high"],
                                            "low": access_settings["bgTarget"][0]["low"]}
            wizard_reading["recommended"] = {}
            wizard_reading["recommended"]["carb"] = tools.round_to(wizard_reading["carbInput"] / wizard_reading["insulinCarbRatio"])
            wizard_reading["recommended"]["correction"] =  0
            wizard_reading["recommended"]["net"] = (tools.round_to(wizard_reading["recommended"]["carb"] 
                                                   + wizard_reading["recommended"]["correction"] - wizard_reading["insulinOnBoard"]))
            normal_or_square = random.randint(0, 9)
            if normal_or_square == 1 or normal_or_square == 2: #decide which type bolus to generate 
                which_bolus = dual_square_bolus
            elif normal_or_square == 3:
                which_bolus = square_bolus 
            else:
                which_bolus = normal_bolus
            
            override  = override_wizard(carb_val)
            if override:
                associated_bolus = which_bolus(override, timestamp, start_time, no_wizard, zonename)
                wizard_reading["bolus"] = associated_bolus["id"]
                wizard_data.append(associated_bolus)
            else:
                associated_bolus = which_bolus(carb_val, timestamp, start_time, no_wizard, zonename)
                wizard_reading["bolus"] = associated_bolus["id"]
                wizard_data.append(associated_bolus)
            
            iob_dict = tools.update_iob_bolus_dict(iob_dict, [associated_bolus], access_settings["actionTime"])
            wizard_data.append(wizard_reading)
    return wizard_data

def override_wizard(carb_val):
    """ Returns a new carb value when the user overrides the recommended bolus
        Otherwise returns False 
    """
    override = random.randint(0,4)
    if override == 3:
        user_overridden_bolus = carb_val + random.randrange(-30, 30, 5)
        if user_overridden_bolus >= 1:
            return user_overridden_bolus
    return False
