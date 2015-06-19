from pytz import timezone
from datetime import datetime, timedelta 

def is_dst(zonename, date):
    local_tz = timezone(zonename)
    localized_time = local_tz.localize(date)
    return localized_time.dst() != timedelta(0)

def get_offset(zonename, date):
    local_tz = timezone(zonename) 
    if is_dst(zonename, date):
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

def format_basal_for_wizard(basal_data):
    """ Retrieve rates, times and duration values from basal data to generate IOB values
        Returns a list of time-basal lists 
    """
    time_vals = []
    for basal_entry in basal_data:
        if basal_entry['type'] == 'basal' and basal_entry['deliveryType'] != 'suspend':
            rate = basal_entry["rate"] #unit per hour
            duration = basal_entry["duration"]/1000/60 #in minutes
            str_time = basal_entry["deviceTime"]
            start_time = datetime.strptime(str_time, '%Y-%m-%dT%H:%M:%S')
            total_insulin_delivered = rate * (duration/60) 
            num_segments = duration / 5 #5 minute segments 
            insulin_per_segment = total_insulin_delivered / num_segments
        next_time = int(start_time.strftime('%s')) #in seconds
        end_date = start_time + timedelta(minutes=duration)
        end_time = int(end_date.strftime('%s'))
        while next_time < end_time:
            time_vals.append([next_time, insulin_per_segment])
            next_time += 5 * 60 #next time -- 5 minutes later (in seconds)  
    return time_vals

def format_bolus_for_wizard(bolus_data):
    """ Retrieve rate times and duration values from bolus data to generate IOB values
        Returns a list of time-bolus lists
    """ 
    time_vals = []
    for bolus_entry in bolus_data:
        str_time = bolus_entry["deviceTime"]
        start_time = datetime.strptime(str_time, '%Y-%m-%dT%H:%M:%S')
        if bolus_entry['subType'] == "normal":
            initial_insulin = bolus_entry["normal"]
            time_vals.append([int(start_time.strftime('%s')), initial_insulin])
        else:
            duration = bolus_entry["duration"]/1000/60 #in minutes
            if duration > 0:
                num_segments = duration / 5 #5 minute segments 
                extended_insulin = bolus_entry["extended"]
                insulin_per_segment = extended_insulin / num_segments
                if bolus_entry['subType'] == "dual/square":
                    initial_insulin = bolus_entry["normal"]
                    time_vals.append([int(start_time.strftime('%s')), initial_insulin])
                next_time = int(start_time.strftime('%s')) #in seconds
                end_date = start_time + timedelta(minutes=duration)
                end_time = int(end_date.strftime('%s'))
                while next_time < end_time:
                    time_vals.append([next_time, insulin_per_segment])
                    next_time += 5 * 60 #next time -- 5 minutes later (in seconds)  
    return time_vals            
        
def creare_iob_dict(bolus_data, action_time):
    """ Return a dictionary with insulin on board values for every timestamp in bolus_data"""
    time_vals = format_bolus_for_wizard(bolus_data)
    iob_dict = {}
    for time_bolus in time_vals:
        remaining_time = action_time * 60 #in minutes
        step = 0 
        time = time_bolus[0]
        initial_value = time_bolus[1]
        slope = initial_value / action_time
        iob_amount = initial_value - slope * step #linear decay equation to calculate IOB at any time 
        if time not in iob_dict:
            iob_dict[time] = iob_amount
        else: 
            iob_dict[time] += iob_amount
        while remaining_time > 5: #continue to calculate iob values until complete decay
            step += 0.08333333333333333 #5 min in hours
            time += 5 * 60 
            iob_amount = initial_value - slope * step
            if time not in iob_dict:
                iob_dict[time] = round_to(iob_amount)
            else: 
                iob_dict[time] += round_to(iob_amount)
            remaining_time -= 5 #subtract 5 minutes from remaining time 
    return iob_dict

def update_iob_bolus_dict(curr_dict, associated_bolus, action_time):
    """ After a new bolus events is generated during a wizard event, update the iob_dict"""
    to_add = creare_iob_dict(associated_bolus, action_time)
    for key in to_add:
        if key in curr_dict:
            curr_dict[key] += to_add[key]
        else:
            curr_dict[key] = to_add[key]
    return curr_dict    

def insulin_on_board(iob_dict, bolus_data, action_time, timestamp):
    """ Return insulin on board for a particular timestamp"""
    if timestamp in iob_dict:
        return iob_dict[timestamp]
    else:
        closest_timestamp = min(iob_dict.keys(), key=lambda k: abs(k-timestamp))
        if abs(timestamp - closest_timestamp) <= 300: #approximate to 5 minutes max
            return iob_dict[closest_timestamp]
        else:
            return 0

def multiply(x, y):
    return x * y

