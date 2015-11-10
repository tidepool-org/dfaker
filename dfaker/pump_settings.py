import random

from . import common_fields
from . import tools


def make_pump_settings(start_time, zonename, pump_name):
    """ Construct a settings object
        start_time -- a datetime object with a timezone
        zonename -- name of timezone in effect
    """
    settings_data = []
    settings = {}
    offset = tools.get_offset(zonename, start_time)
    utc_time = tools.convert_ISO_to_epoch(str(start_time), '%Y-%m-%d %H:%M:%S')
    time_in_seconds = int(utc_time - offset*60)
    settings = common_fields.add_common_fields('pumpSettings', settings,
                                               time_in_seconds, zonename)
    settings["activeSchedule"] = "standard"
    # 3 or 4 hours for insulin to decay completely
    settings["actionTime"] = random.randint(3, 4)
    settings["basalSchedules"] = {
        "standard": [
            {"rate": 0.9, "start": 0},
            {"rate": 0.6, "start": 3600000},
            {"rate": 0.65, "start": 10800000},
            {"rate": 0.8, "start": 14400000},
            {"rate": 0.85, "start": 18000000},
            {"rate": 0.8, "start": 28800000},
            {"rate": 0.75, "start": 32400000},
            {"rate": 0.8, "start": 54000000},
            {"rate": 0.85, "start": 61200000}
        ]
    }
    if pump_name == "Medtronic" or pump_name == "OmniPod":
        settings["carbRatio"] = [
            {"amount": random.randint(9, 15), "start": 0},
            {"amount": random.randint(9, 15), "start": 36000000},
            {"amount": random.randint(9, 15), "start": 72000000}
        ]
        settings["insulinSensitivity"] = [
            {"amount": tools.convert_to_mmol(30), "start": 0},
            {"amount": tools.convert_to_mmol(40), "start": 18000000},
            {"amount": tools.convert_to_mmol(50), "start": 39600000},
            {"amount": tools.convert_to_mmol(35), "start": 68400000}
        ]
        if pump_name == 'Medtronic':
            settings["bgTarget"] = medtronic_settings()
        elif pump_name == 'OmniPod':
            settings["bgTarget"] = omniPod_settings()
    elif pump_name == 'Tandem':
        settings["carbRatios"],
        settings["insulinSensitivities"],
        settings["bgTargets"] = tandem_settings()
    settings["units"] = {"bg": "mg/dL", "carb": "grams"}
    settings_data.append(settings)
    return settings_data


def omniPod_settings():
    target = random.randrange(90, 110, 10)
    bgTarget_high = random.randrange(target + 10, 140, 10)
    bgTarget = [{"high": tools.convert_to_mmol(bgTarget_high),
                 "target": tools.convert_to_mmol(target),
                 "start": 0}]
    return bgTarget


def medtronic_settings():
    bgTarget_low = random.randrange(80, 120, 10)
    bgTarget_high = random.randrange(bgTarget_low + 10, 140, 10)
    bgTarget = [{"high": tools.convert_to_mmol(bgTarget_high),
                 "low": tools.convert_to_mmol(bgTarget_low),
                 "start": 0}]
    return bgTarget


def tandem_settings():
    carb_ratios = {
        'standard': [
            {"amount": random.randint(9, 15), "start": 0},
            {"amount": random.randint(9, 15), "start": 36000000},
            {"amount": random.randint(9, 15), "start": 72000000}
        ]
    }
    insulin_sensitivities = {
        'standard': [
            {"amount": tools.convert_to_mmol(30), "start": 0},
            {"amount": tools.convert_to_mmol(40), "start": 18000000},
            {"amount": tools.convert_to_mmol(50), "start": 39600000},
            {"amount": tools.convert_to_mmol(35), "start": 68400000}
        ]
    }
    target = random.randrange(90, 110, 10)
    bg_targets = {
        'standard': [
            {"target": tools.convert_to_mmol(target), "start": 0}
        ]
    }
    return carb_ratios, insulin_sensitivities, bg_targets
