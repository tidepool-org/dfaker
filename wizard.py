import random
import settings
import common_fields
import tools
import bolus

def wizard(start_time, gluc, carbs, timesteps, zonename):
    wizard_data = []
    access_settings = settings.settings(start_time, zonename)[0]
    for gluc_val, carb_val, timestamp in zip(gluc, carbs, timesteps):
        wizard_reading = {}
        wizard_reading = common_fields.add_common_fields('wizard', wizard_reading, timestamp, zonename)
        wizard_reading["bgInput"] = tools.convert_to_mmol(gluc_val)
        wizard_reading["carbInput"] = int(carb_val)
        wizard_reading["insulinOnBoard"] = 0  
        carb_ratio_sched, sensitivity_sched = access_settings["carbRatio"], access_settings["insulinSensitivity"]
        sensitivity = tools.get_rate_from_settings(sensitivity_sched, wizard_reading["deviceTime"], "insulinSensitivity")
        carb_ratio = tools.get_rate_from_settings(carb_ratio_sched, wizard_reading["deviceTime"], "carbRatio")
        wizard_reading["insulinSensitivity"] = sensitivity
        wizard_reading["insulinCarbRatio"] = carb_ratio
        wizard_reading["bgTarget"] = { "high": access_settings["bgTarget"][0]["high"],
                                        "low": access_settings["bgTarget"][0]["low"]}
        wizard_reading["payload"] = {}
        wizard_reading["recommended"] = {}
        wizard_reading["recommended"]["carb"] = tools.round_to(wizard_reading["carbInput"] / wizard_reading["insulinCarbRatio"])
        wizard_reading["recommended"]["correction"] =  0
        wizard_reading["recommended"]["net"] = (tools.round_to(wizard_reading["recommended"]["carb"] 
                                               + wizard_reading["recommended"]["correction"] - wizard_reading["insulinOnBoard"]))
        normal_or_square = random.randint(0, 9)
        if normal_or_square == 1 or normal_or_square == 2: #decide which type bolus to generate 
            which_bolus = bolus.dual_square_bolus
        elif normal_or_square == 3:
            which_bolus = bolus.square_bolus 
        else:
            which_bolus = bolus.normal_bolus
        
        override  = override_wizard(carb_val)
        if override:
            assosiated_bolus = which_bolus(override, timestamp, start_time, zonename)
            wizard_reading["bolus"] = assosiated_bolus["id"]
            wizard_data.append(assosiated_bolus)
        else:
            assosiated_bolus = which_bolus(carb_val, timestamp, start_time, zonename)
            wizard_reading["bolus"] = assosiated_bolus["id"]
            wizard_data.append(assosiated_bolus)
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