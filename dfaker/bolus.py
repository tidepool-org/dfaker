from datetime import datetime
import numpy as np
import random
import pytz

from . import common_fields
from .pump_settings import make_pump_settings
from . import tools


def generate_boluses(solution, start_time, zonename, zone_offset):
    """ Generates events for both bolus entries and wizard entries.
        Returns carb, time and glucose values for each event
    """
    all_carbs = solution[:, 0]
    glucose = solution[:, 1]
    ts = tools.make_timesteps(start_time, zone_offset, solution[:, 2])
    positives = []
    for row in zip(all_carbs, ts, glucose):  # keep significant carb events
        if row[0] > 10:
            positives.append(row)
    np_pos = np.array(clean_up_boluses(positives))
    cleaned = remove_night_boluses(np_pos, zonename)

    for row in cleaned:  # find carb values that are too high and reduce them
        carb_val = row[0]
        if carb_val > 120:
            row[0] = carb_val / 2
        elif carb_val > 30:
            row[0] = carb_val * 0.75
    bolus, wizard = bolus_or_wizard(cleaned)
    np_bolus, np_wizard = np.array(bolus), np.array(wizard)
    b_carbs, b_ts = np_bolus[:, 0], np_bolus[:, 1]
    w_card, w_ts, w_gluc = np_wizard[:, 0], np_wizard[:, 1], np_wizard[:, 2]
    return b_carbs, b_ts, w_card, w_ts, w_gluc


def clean_up_boluses(carb_time_gluc, filter_rate=7):
    """ Cleans up clusters of carb events based on meal freqeuncy
        carb_time_gluc -- a numpy array of carbohydrates and glucose values
                          at different points in time
        filter_rate -- how many 5 minute segments should be filtered within
                       the range of a single event.
                       Example: 7 * 5 --> remove the next 35 minutes of data
                       from carb_time
    """
    return carb_time_gluc[::filter_rate]


def remove_night_boluses(carb_time_gluc, zonename):
    """Removes night boluses excpet for events with high glucose"""
    keep = []
    for row in carb_time_gluc:
        carb_val = row[0]
        time_val = row[1]
        gluc_val = row[2]
        hour = datetime.fromtimestamp(time_val, pytz.timezone(zonename)).hour
        if hour > 6 and hour < 23:
            keep.append(row)
        # keep if glucose level is high and a high enough insulin dose is given
        elif int(gluc_val) not in range(0, 250) and carb_val > 25:
            keep.append(row)
    np_keep = np.array(keep)
    return np_keep


def bolus_or_wizard(solution):
    """Randomly decide when to generte wizards events that are linked with
       boluses and when to have plain boluses.
       About 2 out of 6 events will be plain boluses
    """
    bolus_events, wizard_events = [], []
    for row in solution:
        bolus_or_wizard = random.randint(0, 5)
        if bolus_or_wizard == 2 or bolus_or_wizard == 4:
            bolus_events.append(row)
        else:
            wizard_events.append(row)
    return bolus_events, wizard_events


def get_carb_ratio(start_time, curr_time, zonename, pump_name):
    """ Get carb ratio from settings
        start_time -- a datetime object in this format: YYYY-MM-DD HH:MM:SS
        curr_time -- a string representation of time in deviceTime
                     format: YYYY-MM-DDTHH:MM:MS
        zonename -- ame of timezone in effect
    """
    pump_settings = make_pump_settings(start_time, zonename, pump_name)[0]
    if pump_name == 'Tandem':
        carb_ratio_sched = pump_settings["carbRatios"]["standard"]
        carb_ratio = tools.get_rate_from_settings(carb_ratio_sched, curr_time,
                                                  "carbRatio")
        return carb_ratio
    carb_ratio_sched = pump_settings["carbRatio"]
    carb_ratio = tools.get_rate_from_settings(carb_ratio_sched, curr_time,
                                              "carbRatio")
    return carb_ratio


def check_bolus_time(timestamp, no_bolus):
    """ Remove any bolus that whose time is within the no_bolus range
        no_bolus -- a list of lists of start and end times during which there
                    should be no bolus events for example, when the pump was
                    suspended
    """
    for duration in no_bolus:
        if int(timestamp) in range(int(duration[0]), int(duration[1]) + 1):
            return False
    return True


def bolus(start_time, carbs, timesteps, no_bolus, zonename, pump_name):
    """ Construct bolus events
        start_time -- a datetime object with a timezone
        carbs -- a list of carb events at each timestep
        timesteps -- a list of epoch times
        no_bolus -- a list of lists of start and end times during which there
                    should be no bolus events for example, when the pump was
                    suspended
        zonename -- name of timezone in effect
    """
    bolus_data = []
    for value, timestamp in zip(carbs, timesteps):
        normal_or_square = random.randint(0, 9)
        # 2 in 10 are dual square
        if normal_or_square == 1 or normal_or_square == 2:
            result = dual_square_bolus(value, timestamp, start_time, no_bolus,
                                       zonename, pump_name)
        elif normal_or_square == 3:  # 1 in 10 is a sqaure bolus
            result = square_bolus(value, timestamp, start_time, no_bolus,
                                  zonename, pump_name)
        else:  # 8 of 10 are normal boluses
            result = normal_bolus(value, timestamp, start_time, no_bolus,
                                  zonename, pump_name)
        if result:
            bolus_data.append(result)
    return bolus_data


def dual_square_bolus(value, timestamp, start_time, no_bolus, zonename,
                      pump_name):
    if check_bolus_time(timestamp, no_bolus):
        bolus_entry = {}
        bolus_entry = common_fields.add_common_fields('bolus', bolus_entry,
                                                      timestamp, zonename)
        bolus_entry["subType"] = "dual/square"
        carb_ratio = get_carb_ratio(start_time, bolus_entry["deviceTime"],
                                    zonename, pump_name)
        insulin = int(value) / carb_ratio
        bolus_entry["normal"] = \
            tools.round_to(random.uniform(insulin / 3, insulin / 2))
        bolus_entry["extended"] = \
            tools.round_to(insulin - bolus_entry["normal"])
        # in ms
        bolus_entry["duration"] = random.randrange(1800000, 5400000, 300000)

        interrupt = random.randint(0, 9)  # interrupt 1 in 10 boluses
        if interrupt == 1:
            bolus_entry = (interrupted_dual_square_bolus(bolus_entry["normal"],
                           bolus_entry["extended"], bolus_entry["duration"],
                           timestamp, zonename))
        return bolus_entry


def square_bolus(value, timestamp, start_time, no_bolus, zonename, pump_name):
    if check_bolus_time(timestamp, no_bolus):
        bolus_entry = {}
        bolus_entry = common_fields.add_common_fields('bolus', bolus_entry,
                                                      timestamp, zonename)
        bolus_entry["subType"] = "square"
        bolus_entry["duration"] = random.randrange(1800000, 5400000, 300000)
        carb_ratio = get_carb_ratio(start_time, bolus_entry["deviceTime"],
                                    zonename, pump_name)
        insulin = tools.round_to(int(value) / carb_ratio)
        bolus_entry["extended"] = insulin
        return bolus_entry


def normal_bolus(value, timestamp, start_time, no_bolus, zonename, pump_name):
    if check_bolus_time(timestamp, no_bolus):
        bolus_entry = {}
        bolus_entry = common_fields.add_common_fields('bolus', bolus_entry,
                                                      timestamp, zonename)
        bolus_entry["subType"] = "normal"
        carb_ratio = get_carb_ratio(start_time, bolus_entry["deviceTime"],
                                    zonename, pump_name)
        insulin = tools.round_to(int(value) / carb_ratio)
        bolus_entry["normal"] = insulin

        interrupt = random.randint(0, 9)  # interrupt 1 in 10 boluses
        if interrupt == 1:
            bolus_entry = interrupted_bolus(insulin, timestamp, zonename)
        return bolus_entry


def interrupted_bolus(value, timestamp, zonename):
    bolus_entry = {}
    bolus_entry = common_fields.add_common_fields('bolus', bolus_entry,
                                                  timestamp, zonename)
    bolus_entry["subType"] = "normal"
    bolus_entry["expectedNormal"] = value
    bolus_entry["normal"] = tools.round_to(value - random.uniform(0, value))
    return bolus_entry


def interrupted_dual_square_bolus(normal, extended, duration, timestamp,
                                  zonename):
    interrupt_normal = random.randint(0, 1)
    bolus_entry = {}
    bolus_entry = common_fields.add_common_fields('bolus', bolus_entry,
                                                  timestamp, zonename)
    bolus_entry["subType"] = "dual/square"
    if interrupt_normal:
        bolus_entry["expectedNormal"] = normal
        bolus_entry["normal"] = \
            tools.round_to(normal - random.uniform(0, normal))
        bolus_entry["extended"] = 0
        bolus_entry["duration"] = 0
        bolus_entry["expectedDuration"] = duration
        bolus_entry["expectedExtended"] = extended
    else:
        interruption_time = random.randrange(300000, duration, 300000)
        rate = extended / duration
        bolus_entry["normal"] = normal
        bolus_entry["expectedDuration"] = duration
        bolus_entry["expectedExtended"] = extended
        bolus_entry["extended"] = tools.round_to(rate * interruption_time)
        bolus_entry["duration"] = interruption_time
    return bolus_entry
