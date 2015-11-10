from datetime import datetime, timedelta
import random
from pytz import timezone

from . import common_fields
from .device_event import suspend_pump, make_status_event
from .pump_settings import make_pump_settings
from . import tools


def scheduled_basal(start_time, num_days, zonename, pump_name):
    """ Construct basal events based on a basal schedule from settings
        start_time -- a datetime object with a timezone
        num_days -- integer reflecting total number of days over which data
                    is generated
        zonename -- name of timezone in effect
    """
    basal_data, pump_suspended = [], []
    pump_settings = make_pump_settings(start_time, zonename=zonename,
                                       pump_name=pump_name)[0]
    offset = tools.get_offset(zonename, start_time)
    utc_time = tools.convert_ISO_to_epoch(str(start_time), '%Y-%m-%d %H:%M:%S')
    next_time = int(utc_time - offset*60)
    seconds_to_add = num_days * 24 * 60 * 60
    end_time = next_time + seconds_to_add
    while next_time < end_time:
        basal_entry = {}
        basal_entry = common_fields.add_common_fields('basal', basal_entry,
                                                      next_time, zonename)
        basal_entry["deliveryType"] = "scheduled"
        basal_entry["scheduleName"] = "standard"

        # get basal schedule from settings
        schedule = pump_settings["basalSchedules"]["standard"]
        basal_entry["rate"], start, corrected_start, end = \
            tools.get_rate_from_settings(schedule, basal_entry["deviceTime"],
                                         "basalSchedules")
        duration = (end - start) / 1000  # in seconds
        zone = timezone(zonename)

        # localize start and end date to get acurate basal times in local
        # time (not in UTC)
        start_date = datetime.fromtimestamp(next_time)
        end_date = datetime.fromtimestamp(next_time + duration)
        localized_start = zone.localize(start_date)
        localized_end = zone.localize(end_date)
        start_offset = tools.get_offset(zonename, start_date)
        end_offset = tools.get_offset(zonename, end_date)
        # account for time chance (DST)
        if start_offset != end_offset:
            diff = end_offset - start_offset
            localized_end = localized_end - timedelta(minutes=diff)
        elapsed_seconds = (localized_end - localized_start).total_seconds()
        if next_time == int(utc_time - offset*60) or start != corrected_start:
            basal_entry["duration"] = end - corrected_start
        else:
            basal_entry["duration"] = int(elapsed_seconds * 1000)
        basal_data.append(basal_entry)

        # Create temp basal event to override scheduled basal

        # avoid temp basal during DST change
        if randomize_temp_basal() and start_offset == end_offset:
            # randomize start of temp basal in ms
            randomize_start = random.randrange(300000, 3000000, 60000)
            start_temp = next_time + randomize_start / 1000
            temp_entry, temp_duration = temp_basal(basal_entry, start_temp,
                                                   zonename=zonename)
            diff = basal_entry["duration"] - randomize_start
            basal_entry["duration"] -= diff
            basal_data.append(temp_entry)
            next_time += ((basal_entry["duration"] / 1000) +
                          (temp_duration / 1000))
        # Create suspened basal event to override scheduled basal
        elif suspend_pump() and start_offset == end_offset:
            basal_entry["deliveryType"] = "suspend"
            del basal_entry["rate"]
            # add device meta pump suspend and resume event
            suspend_event = make_status_event('suspend', next_time, zonename)
            suspend_duration = suspend_event['duration']
            resume_event = make_status_event('resume',
                                             next_time + suspend_duration/1000,
                                             zonename)
            basal_data.append(suspend_event)
            basal_data.append(resume_event)
            basal_entry["duration"] = suspend_duration
            # track start/end times for suspension
            times = [next_time, next_time + basal_entry["duration"]/1000]
            pump_suspended.append(times)
            next_time += basal_entry["duration"] / 1000
        # update time to generate next basal
        else:
            next_time += basal_entry["duration"] / 1000
    return basal_data, pump_suspended


def temp_basal(scheduled_basal, start_time, zonename):
    basal_entry = {}
    basal_entry = (common_fields.add_common_fields('basal', basal_entry,
                                                   start_time, zonename))
    basal_entry["deliveryType"] = "temp"
    # 20min-6hrs
    basal_entry["duration"] = random.randrange(1200000, 21600000, 600000)
    basal_entry["percent"] = random.randrange(5, 195, 10) / 100
    basal_entry["rate"] = scheduled_basal["rate"] * basal_entry["percent"]
    basal_entry["suppressed"] = scheduled_basal
    return basal_entry, basal_entry["duration"]


def randomize_temp_basal():
    # 1 in 10 scheduled basals is overridden with a temp basal
    decision = random.randint(0, 9)
    if decision == 2:
        return True
    return False
