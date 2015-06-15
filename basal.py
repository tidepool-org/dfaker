import random
import common_fields 
import settings
from datetime import datetime, timedelta
from pytz import timezone
import tools

def scheduled_basal(start_time, params):
    basal_data = []  
    access_settings = settings.settings(start_time, params)[0]
    next_time = int(start_time.strftime('%s')) #in seconds
    seconds_to_add = params["num_days"] * 24 * 60 * 60
    end_date = start_time + timedelta(seconds=seconds_to_add)
    end_time = int(end_date.strftime('%s'))
    while next_time < end_time:
        basal_entry = {}
        basal_entry = common_fields.add_common_fields('basal', basal_entry, next_time, params)
        basal_entry["deliveryType"] = "scheduled" #scheduled for now    

        schedule = access_settings["basalSchedules"]["standard"] 
        basal_entry["rate"], start, initial_start, end = tools.get_rate_from_settings(schedule, basal_entry["deviceTime"] , "basalSchedules")
        duration = (end - start) / 1000 #in seconds

        zone = timezone(params['zone'])
        start_date = datetime.fromtimestamp(next_time)
        localized_start = zone.localize(start_date)
        end_date = datetime.fromtimestamp(next_time + duration)
        localized_end = zone.localize(end_date)
        offset1 = tools.get_offset(params['zone'], start_date)
        offset2 = tools.get_offset(params['zone'], end_date)

        if offset1 != offset2:
            diff = offset2 - offset1
            localized_end = localized_end - timedelta(minutes=diff)
        total_seconds = (localized_end - localized_start).total_seconds()
        if next_time == int(start_time.strftime('%s')):
            basal_entry["duration"] = end - initial_start
        else:
            basal_entry["duration"] = int(total_seconds * 1000)
        basal_entry["scheduleName"] = "standard"
       
        if randomize_temp_basal(): #create temp basal if true
            basal_data.append(temp_basal(basal_entry, next_time, params))
        next_time += basal_entry["duration"] / 1000
        basal_data.append(basal_entry)
    return basal_data

def temp_basal(scheduled_basal, timestamp, params):
    basal_entry = {}
    basal_entry = common_fields.add_common_fields('basal', basal_entry, timestamp, params)
    basal_entry["deliveryType"] = "temp"
    basal_entry["duration"] = scheduled_basal["duration"]
    basal_entry["percent"] = random.randrange(0, 80, 5) / 100
    basal_entry["rate"] = scheduled_basal["rate"] * basal_entry["percent"]
    basal_entry["suppressed"] = scheduled_basal
    return basal_entry

def randomize_temp_basal():
    decidion = random.randint(0,9) #1 in 10 scheduled basals is overridden with a temp basal
    if decidion == 2:
        return True
    return False