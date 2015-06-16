from pytz import timezone
from datetime import datetime, timedelta 

def is_dst(zonename, date):
    local_tz = timezone(zonename)
    localized_time = local_tz.localize(date)
    return localized_time.dst() != timedelta(0)

def get_offset(zonename, date):
    local_tz = timezone(zonename) 
    if is_dst(date, zone):
        return - (24 * 60 - local_tz.utcoffset(date, is_dst=True).seconds / 60)
    else:
        return - (24 * 60 - local_tz.utcoffset(date, is_dst=False).seconds / 60) 

def convert_to_mmol(iterable):
    conversion_factor = 18.01559
    if isinstance(iterable, float) or isinstance(iterable, int):
        return iterable / conversion_factor
    return [reading / conversion_factor for reading in iterable]

def round_to(n, precision=0.005):
    """ The round function can take positive or negative values
        and round them to a certain precision.
        In the fake data generator, only positive values are being passed into it
    """
    if n >= 0:
        correction = 0.5 
    else:
        correction = -0.5
    result = int(n / precision + correction) * precision
    return round(result, 3)

def make_timesteps(start_timestamp, timelist):
    """ Convert list of floats representing time into epoch time"""
    timesteps = []
    epoch_ts = start_timestamp.strftime('%s')
    for time_item in timelist:
        new_time = int(epoch_ts) + int(time_item * 60) 
        timesteps.append(new_time)
    return timesteps

def get_rate_from_settings(schedule, time, name):
    """Obtains a rate or amount from settings based on time of day
       If name is basalSchedules, returns rate as well as start and stop times
       Otherwise, if name is carbRatio or insulinSensitivity, returns just amount
    """
    t = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S')
    if name == "basalSchedules": #account for variation in naming 
        value_name = "rate" #set initial rate
    else:
        value_name = "amount"
    ms_since_midnight = t.hour*60*60*1000 + t.minute*60*1000 + t.second*1000
    last_segment = schedule[len(schedule)-1]
    full_day = 86400000 #24 hours in ms
    rate = schedule[0][value_name] #set initial rate
    initial_start = ms_since_midnight #set initial start time
    for segment in schedule:
        end = segment["start"]
        if ms_since_midnight < segment["start"]:
            break
        elif ms_since_midnight >= last_segment["start"]:
            start = last_segment["start"]
            end = full_day
            rate = last_segment[value_name]
            break
        start = segment["start"]
        rate = segment[value_name] #update rate to next segment rate
    if name == "basalSchedules":
        return rate, start, initial_start, end 
    return rate #only rate needed for insulin sensitivity/carb ratio events