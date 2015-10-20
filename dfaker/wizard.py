import random

from .bolus import (square_bolus, normal_bolus, dual_square_bolus,
                    check_bolus_time)
from . import common_fields
from . import insulin_on_board
from . import settings
from . import tools


def wizard(start_time, gluc, carbs, timesteps, bolus_data, no_wizard,
           zonename, pump_name):
    """ Construct a wizard event
        start_time -- a datetime object with a timezone
        gluc -- a list of glucose values at each timestep
        carbs -- a list of carb events at each timestep
        timesteps -- a list of epoch times
        bolus_data -- of list of bolus data dictionaries to calculate IOB
        no_wizard -- a list of lists of start and end times (in epoch time)
                     during which there should be no bolus events, for example,
                     if the pump is suspended
        zonename -- name of timezone in effect
    """
    wizard_data = []
    access_settings = settings.settings(start_time, zonename, pump_name)[0]
    iob_dict = insulin_on_board.create_iob_dict(bolus_data,
                                                access_settings["actionTime"])
    for gluc_val, carb_val, timestamp in zip(gluc, carbs, timesteps):
        if check_bolus_time(timestamp, no_wizard):
            wizard_reading = {}
            wizard_reading = common_fields.add_common_fields('wizard',
                                                             wizard_reading,
                                                             timestamp,
                                                             zonename)
            wizard_reading["bgInput"] = tools.convert_to_mmol(gluc_val)
            wizard_reading["carbInput"] = int(carb_val)
            iob = insulin_on_board.insulin_on_board(iob_dict, int(timestamp))
            wizard_reading["insulinOnBoard"] = tools.convert_to_mmol(iob)

            # pump specific input:
            if pump_name == 'Medtronic' or pump_name == 'OmniPod':
                carb_ratio_sched = access_settings["carbRatio"]
                sensitivity_sched = access_settings["insulinSensitivity"]

                if pump_name == 'Medtronic':
                    wizard_reading["bgTarget"] = {
                        "high": access_settings["bgTarget"][0]["high"],
                        "low": access_settings["bgTarget"][0]["low"]
                    }
                elif pump_name == 'OmniPod':
                    wizard_reading["bgTarget"] = {
                        "high": access_settings["bgTarget"][0]["high"],
                        "target": access_settings["bgTarget"][0]["target"]
                    }
            elif pump_name == 'Tandem':
                target = access_settings["bgTargets"]["standard"][0]["target"]
                wizard_reading["bgTarget"] = {"target": target}
                carb_ratio_sched = access_settings["carbRatios"]["standard"]
                sensitivity_sched = \
                    access_settings["insulinSensitivities"]["standard"]

            sensitivity = tools.get_rate_from_settings(
                              sensitivity_sched, wizard_reading["deviceTime"],
                              "insulinSensitivity")
            carb_ratio = tools.get_rate_from_settings(
                             carb_ratio_sched, wizard_reading["deviceTime"],
                             "carbRatio")
            wizard_reading["insulinSensitivity"] = sensitivity
            wizard_reading["insulinCarbRatio"] = carb_ratio

            wizard_reading["recommended"] = {}
            carb = (wizard_reading["carbInput"] /
                    wizard_reading["insulinCarbRatio"])
            wizard_reading["recommended"]["carb"] = tools.round_to(carb)
            wizard_reading["recommended"]["correction"] = 0
            corrected_carb = (wizard_reading["recommended"]["carb"] +
                              wizard_reading["recommended"]["correction"])
            iob = tools.round_to(wizard_reading["insulinOnBoard"])
            wizard_reading["recommended"]["net"] = (corrected_carb - iob)
            wizard_reading["units"] = "mmol/L"
            normal_or_square = random.randint(0, 9)
            if normal_or_square == 1 or normal_or_square == 2:
                bolus_func = dual_square_bolus
            elif normal_or_square == 3:
                bolus_func = square_bolus
            else:
                bolus_func = normal_bolus

            override = override_wizard_random(carb_val)
            if override:
                associated_bolus = bolus_func(
                                       override, timestamp, start_time,
                                       no_wizard, zonename, pump_name)
                wizard_reading["bolus"] = associated_bolus["id"]
                wizard_data.append(associated_bolus)
            else:
                associated_bolus = bolus_func(
                                       carb_val, timestamp, start_time,
                                       no_wizard, zonename, pump_name)
                wizard_reading["bolus"] = associated_bolus["id"]
                wizard_data.append(associated_bolus)

            iob_dict = insulin_on_board.update_iob_dict(
                           iob_dict, [associated_bolus],
                           access_settings["actionTime"])
            wizard_data.append(wizard_reading)
    return wizard_data, iob_dict


def override_wizard_random(carb_val):
    """ Returns a new carb value when the user overrides the recommended bolus
        Otherwise returns False
    """
    override = random.randint(0, 4)
    if override == 3:
        user_overridden_bolus = carb_val + random.randrange(-30, 30, 5)
        if user_overridden_bolus >= 1:
            return user_overridden_bolus
    return False
