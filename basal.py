import random
import common_fields 
import settings
from datetime import datetime, timedelta
from pytz import timezone
import tools

def scheduled_basal(start_time, num_days, zonename):
    """ Construct basal events based on a basal schedule from settings
        start_time -- a datetime object with a timezone
        num_days -- integer reflecting total number of days over which data is generated
        zonename -- name of timezone in effect
    """
    basal_data = []  
    access_settings = settings.settings(start_time, zonename=zonename)[0]
    next_time = int(start_time.strftime('%s')) #in seconds
    seconds_to_add = num_days * 24 * 60 * 60
    end_date = start_time + timedelta(seconds=seconds_to_add)
    end_time = int(end_date.strftime('%s'))
    while next_time < end_time:
        basal_entry = {}
        basal_entry = common_fields.add_common_fields('basal', basal_entry, next_time, zonename)
        basal_entry["deliveryType"] = "scheduled"   
        schedule = access_settings["basalSchedules"]["standard"] 
        basal_entry["rate"], start, initial_start, end = tools.get_rate_from_settings(schedule, basal_entry["deviceTime"] , "basalSchedules")
        duration = (end - start) / 1000 #in seconds
        zone = timezone(zonename)
        start_date, end_date = datetime.fromtimestamp(next_time), datetime.fromtimestamp(next_time + duration)
        localized_start, localized_end = zone.localize(start_date), zone.localize(end_date)
        start_offset, end_offset = tools.get_offset(zonename, start_date), tools.get_offset(zonename, end_date)
        if start_offset != end_offset:
            diff = end_offset - start_offset
            localized_end = localized_end - timedelta(minutes=diff)
        elapsed_seconds = (localized_end - localized_start).total_seconds()
        if next_time == int(start_time.strftime('%s')):
            basal_entry["duration"] = end - initial_start
        else:
            basal_entry["duration"] = int(elapsed_seconds * 1000)
        basal_entry["scheduleName"] = "standard"
       
        if randomize_temp_basal(): #create temp basal if true
            basal_data.append(temp_basal(basal_entry, next_time, zonename=zonename))
        
        if randomize_temp_basal():
            basal_data.append(suspended_basal(basal_entry, next_time, zonename=zonename))    

        next_time += basal_entry["duration"] / 1000
        basal_data.append(basal_entry)
    return basal_data

def temp_basal(scheduled_basal, timestamp, zonename):
    basal_entry = {}
    basal_entry = common_fields.add_common_fields('basal', basal_entry, timestamp, zonename)
    basal_entry["deliveryType"] = "temp"
    basal_entry["duration"] = scheduled_basal["duration"] 
    basal_entry["percent"] = random.randrange(0, 80, 5) / 100
    basal_entry["rate"] = scheduled_basal["rate"] * basal_entry["percent"]
    basal_entry["suppressed"] = scheduled_basal
    return basal_entry

def suspended_basal(scheduled_basal, timestamp, zonename):
    basal_entry = {}
    basal_entry = common_fields.add_common_fields('basal', basal_entry, timestamp, zonename)
    basal_entry["deliveryType"] = "suspend"
    basal_entry["duration"] = scheduled_basal["duration"]
    basal_entry["suppressed"] = scheduled_basal
    return basal_entry


def randomize_temp_basal():
    decidion = random.randint(0,9) #1 in 10 scheduled basals is overridden with a temp basal
    if decidion == 2:
        return True
    return False