from datetime import datetime, timedelta
import random
from pytz import timezone

from . import common_fields 
from .device_meta import suspend_pump, device_meta
from . import settings
from . import tools

def scheduled_basal(start_time, num_days, zonename):
    """ Construct basal events based on a basal schedule from settings
        start_time -- a datetime object with a timezone
        num_days -- integer reflecting total number of days over which data is generated
        zonename -- name of timezone in effect
    """
    basal_data, pump_suspended = [], []  
    access_settings = settings.settings(start_time, zonename=zonename)[0]
    next_time = int(start_time.strftime('%s')) #in seconds
    seconds_to_add = num_days * 24 * 60 * 60
    end_date = start_time + timedelta(seconds=seconds_to_add)
    end_time = int(end_date.strftime('%s'))
    while next_time < end_time:
        basal_entry = {}
        basal_entry = common_fields.add_common_fields('basal', basal_entry, next_time, zonename)
        basal_entry["deliveryType"] = "scheduled"   
        basal_entry["scheduleName"] = "standard"
        schedule = access_settings["basalSchedules"]["standard"] 
        basal_entry["rate"], start, corrected_start, end = tools.get_rate_from_settings(schedule, basal_entry["deviceTime"] , "basalSchedules")
        duration = (end - start) / 1000 #in seconds
        zone = timezone(zonename)
        start_date, end_date = datetime.fromtimestamp(next_time), datetime.fromtimestamp(next_time + duration)
        localized_start, localized_end = zone.localize(start_date), zone.localize(end_date)
        start_offset, end_offset = tools.get_offset(zonename, start_date), tools.get_offset(zonename, end_date)
        if start_offset != end_offset:
            diff = end_offset - start_offset
            localized_end = localized_end - timedelta(minutes=diff)
        elapsed_seconds = (localized_end - localized_start).total_seconds()
        if next_time == int(start_time.strftime('%s')) or start != corrected_start:
            basal_entry["duration"] = end - corrected_start 
        else:
            basal_entry["duration"] = int(elapsed_seconds * 1000)
        basal_data.append(basal_entry)
       
        if randomize_temp_basal() and start_offset == end_offset: #avoid temp basal during DST change
            randomize_start = random.randrange(300000, 3000000, 60000) #randomize start of temp basal in ms  
            start_temp = next_time + randomize_start/1000 
            temp_entry, temp_duration = temp_basal(basal_entry, start_temp, zonename=zonename)
            diff = basal_entry["duration"] - randomize_start
            basal_entry["duration"] -= diff
            basal_data.append(temp_entry)
            next_time += (basal_entry["duration"] / 1000) + (temp_duration / 1000)
        elif suspend_pump() and start_offset == end_offset:
            basal_entry["deliveryType"] = "suspend" 
            del basal_entry["rate"]
            meta_entry, suspend_duration = device_meta(next_time, zonename)
            basal_data.append(meta_entry)
            basal_entry["duration"] = suspend_duration
            pump_suspended.append([next_time, next_time + basal_entry["duration"]/1000]) #keep track of start/end times for suspension 
            next_time += basal_entry["duration"] / 1000 
        else:
            next_time += basal_entry["duration"] / 1000
    return basal_data, pump_suspended

def temp_basal(scheduled_basal, start_time, zonename):
    basal_entry = {}
    basal_entry = (common_fields.add_common_fields('basal', basal_entry, start_time, zonename)) 
    basal_entry["deliveryType"] = "temp"
    basal_entry["duration"] = random.randrange(1200000, 21600000, 600000) #20min-6hrs
    basal_entry["percent"] = random.randrange(5, 195, 10) / 100
    basal_entry["rate"] = scheduled_basal["rate"] * basal_entry["percent"]
    basal_entry["suppressed"] = scheduled_basal
    return basal_entry, basal_entry["duration"]

def randomize_temp_basal():
    decision = random.randint(0,9) #1 in 10 scheduled basals is overridden with a temp basal
    if decision == 2:
        return True
    return False