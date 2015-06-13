import random
import common_fields 
import settings
from datetime import datetime, timedelta

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
        t = datetime.strptime(basal_entry["deviceTime"], '%Y-%m-%dT%H:%M:%S')
        ms_since_midnight = t.hour*60*60*1000 + t.minute*60*1000 + t.second*1000

        last_segment = schedule[len(schedule)-1]
        full_day = 86400000 #24 hours in ms
        basal_entry["rate"] = schedule[0]["rate"] #set initial rate
        initial_start = ms_since_midnight #set initial start time
        for segment in schedule:
            end = segment["start"]
            if ms_since_midnight < segment["start"]:
                break
            elif ms_since_midnight >= last_segment["start"]:
                start = last_segment["start"]
                end = full_day
                basal_entry["rate"] = last_segment["rate"]
                break
            start = segment["start"]
            basal_entry["rate"] = segment["rate"] #update rate to next segment rate

        if next_time == int(start_time.strftime('%s')):
            basal_entry["duration"] = end - initial_start
        else:
            basal_entry["duration"] = end - start
        basal_entry["scheduleName"] = "standard"
        next_time += basal_entry["duration"] / 1000
        basal_data.append(basal_entry)
    return basal_data