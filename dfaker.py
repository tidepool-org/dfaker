#usage: dfaker.py [-h] [-z ZONE] [-d DATE] [-t TIME] [-n NUM_DAYS] [-f FILE]
#                 [-m] [-g] [-s SMBG_FREQ]
#
#optional arguments:
# -h,           --help               show this help message and exit
# -z ZONE,      --timezone ZONE      Local timezone
# -d DATE,      --date DATE          Date in the following format: YYYY-MM-DD
# -t TIME,      --time TIME          Time in the following format: HH:MM
# -n NUM_DAYS,  --num_days NUM_DAYS  Number of days to generate data
# -f FILE,      --output_file FILE   Name of output json file
# -m,           --minify             Minify the json file
# -g,           --gaps               Add gaps to fake data
# -s SMBG_FREQ, --smbg SMBG_FREQ     Freqency of fingersticks a day: high, average or low

from datetime import datetime, timedelta, tzinfo
import time
from pytz import timezone
import pytz
import uuid
import json
import argparse 
import sys
import cbg_equation
import statsmodels.api as sm
import random
import numpy as np 

params = {
    'datetime' : datetime.strptime('2015-03-03 0:0', '%Y-%m-%d %H:%M'),  #default datetime settings
    'zone' : 'US/Pacific', #default zone
    'num_days' : 10, #default number of days to generate data for
    'file' : 'device-data.json', #default json file name 
    'minify' : False, #compact storage option false by default 
    'gaps' : False, #randomized gaps in data, off by default 
    'smbg_freq' : 6 #default number of fingersticks per day
}

def parse(args, params):
    if args.date:
        try:
            d = datetime.strptime(args.date, '%Y-%m-%d')
            year, month, day = d.year, d.month, d.day
            params['datetime'] = params['datetime'].replace(year=year, month=month, day=day)
        except:     
            print('Wrong date format: {:s}. Please enter date as YYYY-MM-DD'.format(args.date))
            sys.exit(1)

    if args.time:
        try:
            t = datetime.strptime(args.time, '%H:%M')
            hour, minute = t.hour, t.minute
            params['datetime'] = params['datetime'].replace(hour=hour, minute=minute)

        except:
            print('Wrong time format: {:s}. Please enter time as HH:MM'.format(args.time))
            sys.exit(1)
     
    if args.zone:
        if args.zone not in pytz.common_timezones:
            print('Unrecognized zone: {:s}'.format(args.zone))
            sys.exit(1)
        params['zone'] = args.zone

    if args.num_days:
        try:
            params['num_days'] = int(args.num_days)
        except:
            print('Wrong input, num_days argument should be a number')
            sys.exit(1)

    if args.file:
        if args.file[-5:] != '.json':
            print('Output file name should have a .json extension')
            sys.exit(1)
        params['file'] = args.file

    if args.minify:
        params['minify'] = True

    if args.gaps:
        params['gaps'] = True

    if args.smbg_freq:
        if args.smbg_freq == 'high':
            params['smbg_freq'] = 8
        elif args.smbg_freq == 'average':
            params['smbg_freq'] = 6
        elif args.smbg_freq == 'low':
            params['smbg_freq'] = 3
        else:
            print('Invalid frequency: {:s}. Please choose between high, average and low'.format(args.smbg_freq))
            sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument('-z', '--timezone', dest='zone', help='Local timezone')
parser.add_argument('-d', '--date', dest='date', help='Date in the following format: YYYY-MM-DD')
parser.add_argument('-t', '--time', dest='time', help='Time in the following format: HH:MM')
parser.add_argument('-n', '--num_days', dest='num_days', help='Number of days to generate data')
parser.add_argument('-f', '--output_file', dest='file', help='Name of output json file')
parser.add_argument('-m', '--minify', dest='minify', action='store_true', help='Minify the json file')
parser.add_argument('-g', '--gaps', dest='gaps', action='store_true', help='Add gaps to fake data')
parser.add_argument('-s', '--smbg', dest='smbg_freq', help='Freqency of fingersticks a day: high, average or low')
args = parser.parse_args()
parse(args, params)

def apply_loess(params, solution):
    """Solves the blood glucose equation over specified period of days 
        and applies a loess smoothing regression to the data 
        Returns numpy arrays for glucose and time values 
    """
    #solving for smbg values
    smbg_gluc = solution[:, 1]
    smbg_time = solution[:, 2]

    #make gaps in cbg data, if needed
    solution = gaps(solution)
    #solving for cbg values 
    cbg_gluc = solution[:, 1]
    cbg_time = solution[:, 2]
    #smoothing blood glucose eqn
    lowess = sm.nonparametric.lowess
    smoothing_distance = 1.4 #1.4 minutes
    fraction = (smoothing_distance / (params['num_days'] * 60 * 24)) * 100
    result = lowess(cbg_gluc, cbg_time, frac=fraction, is_sorted=True)
    smoothed_cbg_time = result[:, 0]
    smoothed_cbg_gluc = result[:, 1]
    return smoothed_cbg_gluc, smoothed_cbg_time, smbg_gluc, smbg_time

def get_offset(zone, date):
    local_tz = timezone(zone)   
    return - (24 * 60 - local_tz.utcoffset(date).seconds / 60) 

def gaps(data):
    """ Create randomized gaps in fake data if user selects the gaps option
        Returns data with gaps if gaps are selected, otherwise returns full data set 
    """
    if params["gaps"]:
        solution_list = solution.tolist()
        gap_list = create_gap_list(params, solution)
        for gap in gap_list:
            solution_list = remove_gaps(solution_list, gap[0], gap[1])
        new_solution = np.array(solution_list)
        return new_solution
    return data

def create_gap_list(params, time_gluc):
    """ Returns sorted list of lists that represent indecies to be removed.
        Each inner list is a two element list containing a start index and an end index
    """
    gaps = random.randint(1 * params['num_days'], 3 * params['num_days']) # amount of gaps  
    gap_list = []
    for _ in range(gaps):
        gap_length = random.randint(10, 40) # length of gaps in 5-min segments
        start_index = random.randint(0, len(time_gluc)) 
        if start_index + gap_length > len(time_gluc):
            end_index = len(time_gluc) - 5
        else:
            end_index = start_index + gap_length
        gap_list.append([start_index, end_index])
    gap_list.sort()
    gap_list.reverse()
    return gap_list 

def remove_gaps(data, start, end):
    return data[:start] + data[end:]

def remove_night_smbg(gluc, timesteps):
    """ Remove most smbg night events """
    keep = []
    for row in zip(gluc, timesteps):
        hour = datetime.fromtimestamp(row[1]).hour
        night_smbg = random.randint(0, 4) #keep some random night smbg events 
        if hour > 6 and hour < 24:
            keep.append(row)
        elif night_smbg == 2:
            keep.append(row)
    return keep
        
def randomize_smbg(time_gluc):
    """ Randomize smbg times according to fingerstick frequency """
    fingersticks_per_day = params["smbg_freq"]
    total = (24 * 60) / 5 
    increment = int(total / fingersticks_per_day)
    start, keep = 0, []
    while start < len(time_gluc):
        try:
            index = random.randint(start, start + increment)
            keep.append(time_gluc[index])
            start += increment
        except:
            break
    return keep

def generate_boluses(solution, start_time):
    """ Generates events for both bolus entries and wizard entries.
        Returns carb, time and glucose values for each event
    """
    all_carbs = solution[:, 0]
    glucose = solution[:,1]
    time = solution[:, 2]
    ts = make_timesteps(start_time, solution[:,2])
    positives = []
    for row in zip(all_carbs, ts, glucose): #keep significant carb events
        if row[0] > 10:
            positives.append(row)
    np_pos = np.array(clean_up_boluses(positives))
    cleaned = remove_night_boluses(np_pos)

    for row in cleaned: #find carb values that are too high and reduce them
        carb_val = row[0]
        if carb_val > 120:
            row[0] = carb_val / 2   
        elif carb_val > 30:
            row[0] = carb_val * 0.75
    bolus, wizard = bolus_or_wizard(cleaned)
    np_bolus, np_wizard = np.array(bolus), np.array(wizard)
    b_carbs, b_ts  = np_bolus[:, 0], np_bolus[:, 1]
    w_card, w_ts, w_gluc = np_wizard[:, 0], np_wizard[:, 1], np_wizard[:,2]
    return b_carbs, b_ts, w_card, w_ts, w_gluc

def clean_up_boluses(carb_time_gluc, filter_rate=7):
    """ Cleans up clusters of carb events based on meal freqeuncy
        carb_time_gluc -- a numpy array of carbohydrates and glucose values at different points in time
        filter_rate -- how many 5 minute segments should be filtered within the range
                       of a single event.
                       Example: 7 * 5 --> remove the next 35 minutes of data from carb_time
    """
    return carb_time_gluc[::filter_rate]

def remove_night_boluses(carb_time_gluc):
    """Removes night boluses excpet for events with high glucose""" 
    keep = []
    for row in carb_time_gluc:
        time_val = row[1]
        gluc_val = row[2]
        hour = datetime.fromtimestamp(time_val).hour
        if hour > 6 and hour < 23:
            keep.append(row)
        elif int(gluc_val) not in range(0,250):
            keep.append(row)
    np_keep = np.array(keep)
    return np_keep

def bolus_or_wizard(solution):
    """Randomely decide when to generte wizards events that are linked with boluses 
       and when to have plain boluses.
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

def add_common_fields(name, datatype, timestamp, params):
    """Populate common fields applicable to all datatypes
       datatype -- a dictionary for a specific data type 
    """
    datatype["type"] = name
    datatype["deviceId"] = "DemoData-123456789"
    datatype["uploadId"] = "upid_abcdefghijklmnop"
    datatype["id"] = str(uuid.uuid4())
    datatype["timezoneOffset"] = get_offset(params['zone'], datetime.fromtimestamp(timestamp))
    datatype["deviceTime"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp + datatype["timezoneOffset"]*60))
    datatype["time"] = (time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp)))
    return datatype

def cbg(gluc, timesteps, params):
    for value, timestamp in zip(gluc, timesteps):
        cbg_reading = {}
        cbg_reading = add_common_fields('cbg', cbg_reading, timestamp, params)
        cbg_reading["value"] = convert_to_mmol(value)
        cbg_reading["units"] = "mmol/L"
        if value >= 400:
            cbg_reading["annotation"] = [{"code": "bg/out-of-range", "threshold": 400, "value": "high"}]
            cbg_reading["value"] = convert_to_mmol(401)
        elif value <= 40:
            cbg_reading["annotation"] = [{"code": "bg/out-of-range", "threshold": 40, "value": "low"}]
            cbg_reading["value"] = convert_to_mmol(39)
        dfaker.append(cbg_reading)

def smbg(gluc, timesteps, params):
    remove_night = remove_night_smbg(gluc, timesteps)   
    time_gluc = randomize_smbg(remove_night)
    for value, timestamp in time_gluc:
        randomize_time = random.randrange(-5000, 5000)
        smbg_reading = {}
        smbg_reading = add_common_fields('smbg', smbg_reading, timestamp, params)
        smbg_reading["value"] = convert_to_mmol(value) + random.uniform(-1.5, 1.5) #in mmol/L
        if value >= 600:
            smbg_reading["annotation"] = [{"code": "bg/out-of-range", "threshold": 600, "value": "high"}]
            smbg_reading["value"] = convert_to_mmol(601)
        elif value <= 20:
            smbg_reading["annotation"] = [{"code": "bg/out-of-range", "threshold": 40, "value": "low"}]
            smbg_reading["value"] = convert_to_mmol(19)
        smbg_reading["units"] = "mmol/L"
        dfaker.append(smbg_reading)

def bolus(carbs, timesteps, params):
    access_settings = dfaker[0]
    carb_ratio = access_settings["carbRatio"][0]["amount"]
    for value, timestamp in zip(carbs, timesteps):      
        normal_or_square = random.randint(0, 4)
        if normal_or_square == 3:
            dual_square_bolus(value, timestamp, carb_ratio, params)
        else:
            normal_bolus(value, timestamp, carb_ratio, params)

def dual_square_bolus(value, timestamp, carb_ratio, params):
    bolus_entry = {}
    bolus_entry = add_common_fields('bolus', bolus_entry, timestamp, params)
    bolus_entry["subType"] = "dual/square"
    insulin = int(value) / carb_ratio
    bolus_entry["normal"] = round_to(random.uniform(insulin / 3, insulin / 2)) 
    bolus_entry["extended"] = round_to(insulin - bolus_entry["normal"]) 
    bolus_entry["duration"] = random.randrange(1800000, 5400000, 300000) #in ms
    dfaker.append(bolus_entry)
    return bolus_entry

def square_bolus(value, timestamp, carb_ratio, params):
    bolus_entry = {}
    bolus_entry = add_common_fields('bolus', bolus_entry, timestamp, params)
    bolus_entry["subType"] = "square"
    bolus_entry["duration"] = random.randrange(1800000, 5400000, 300000)
    insulin = round_to(int(value) / carb_ratio)
    bolus_entry["extended"] = insulin

def normal_bolus(value, timestamp, carb_ratio, params):
    bolus_entry = {}
    bolus_entry = add_common_fields('bolus', bolus_entry, timestamp, params)
    bolus_entry["subType"] = "normal"
    insulin = round_to(int(value) / carb_ratio)
    bolus_entry["normal"] = insulin

    interrupt = random.randint(0,9) #interrupt 1 in 10 boluses
    if interrupt == 1:
        bolus_entry = interrupted_bolus(insulin, timestamp, params)
    dfaker.append(bolus_entry)
    return bolus_entry

def interrupted_bolus(value, timestamp, params):
    bolus_entry = {}
    bolus_entry = add_common_fields('bolus', bolus_entry, timestamp, params)
    bolus_entry["expectedNormal"] = value
    bolus_entry["normal"] = round_to(value - random.uniform(0, value))
    return bolus_entry

def wizard(gluc, carbs, timesteps, params):
    access_settings = dfaker[0]
    for gluc_val, carb_val, timestamp in zip(gluc, carbs, timesteps):
        wizard_reading = {}
        wizard_reading = add_common_fields('wizard', wizard_reading, timestamp, params)
        wizard_reading["bgInput"] = convert_to_mmol(gluc_val)
        wizard_reading["carbInput"] = int(carb_val)
        wizard_reading["insulinOnBoard"] = 0
        wizard_reading["insulinCarbRatio"] = access_settings["carbRatio"][0]["amount"]
        wizard_reading["insulinSensitivity"] = access_settings["insulinSensitivity"][0]["amount"]
        wizard_reading["bgTarget"] = { "high": access_settings["bgTarget"][0]["high"],
                                        "low": access_settings["bgTarget"][0]["low"]}
        wizard_reading["payload"] = {}
        wizard_reading["recommended"] = {}
        wizard_reading["recommended"]["carb"] = round_to(wizard_reading["carbInput"] / wizard_reading["insulinCarbRatio"])
        wizard_reading["recommended"]["correction"] =  0
        wizard_reading["recommended"]["net"] = (round_to(wizard_reading["recommended"]["carb"] 
                                               + wizard_reading["recommended"]["correction"] - wizard_reading["insulinOnBoard"]))
        carb_ratio = access_settings["carbRatio"][0]["amount"]
        normal_or_square = random.randint(0, 4)
        if normal_or_square == 3: #decide which bolus to generate 
            bolus = dual_square_bolus
        else:
            bolus = normal_bolus
        override  = override_wizard(carb_val)
        if override:
            wizard_reading["bolus"] = bolus(override, timestamp, carb_ratio, params)["id"]
        else:
            wizard_reading["bolus"] = bolus(carb_val, timestamp, carb_ratio, params)["id"]
        dfaker.append(wizard_reading)

def override_wizard(carb_val):
    """ Returns a new carb value when the user overrides the recommended bolus
        Otherwise returns False 
    """
    override = random.randint(0,4)
    if override == 3:
        user_overridden_bolus = carb_val + random.randrange(-30, 30, 5)
        if user_overridden_bolus >= 1:
            return user_overridden_bolus
    return False

def scheduled_basal(start_time, params):
    access_settings = dfaker[0]
    next_time = int(start_time.strftime('%s')) #in seconds
    seconds_to_add = params["num_days"] * 24 * 60 * 60
    end_date = start_time + timedelta(seconds=seconds_to_add)
    end_time = int(end_date.strftime('%s'))
    while next_time < end_time:
        basal_entry = {}
        basal_entry = add_common_fields('basal', basal_entry, next_time, params)
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
        dfaker.append(basal_entry)
        
def settings(start_time, params):
    settings = {}
    time_in_seconds = int(start_time.strftime('%s'))
    settings = add_common_fields('settings', settings, time_in_seconds, params)
    settings["activeSchedule"] = "standard"
    settings["basalSchedules"] =  {"standard": [{"rate": 0.9, "start": 0},
                                                {"rate": 0.6, "start": 3600000},
                                                {"rate": 0.65, "start": 10800000},
                                                {"rate": 0.8, "start": 14400000},
                                                {"rate": 0.85, "start": 18000000},
                                                {"rate": 0.8, "start": 28800000},
                                                {"rate": 0.75, "start": 32400000},
                                                {"rate": 0.8, "start": 54000000},
                                                {"rate": 0.85, "start": 61200000}]}
    bgTarget_low = random.randrange(80, 120, 10)
    bgTarget_high = random.randrange(bgTarget_low, 140, 10)
    settings["bgTarget"] = [{"high": convert_to_mmol(bgTarget_high), 
                             "low": convert_to_mmol(bgTarget_low), 
                             "start": 0}]
    settings["carbRatio"] = [ {"amount": random.randint(9, 15), "start": 0}]
    settings["insulinSensitivity"] = [{"amount": convert_to_mmol(50), "start": 0}]
    settings["units"] = { "bg": "mg/dL","carb": "grams"}
    dfaker.append(settings)

dfaker = [] 
solution = cbg_equation.stitch_func(params['num_days'])

d = params['datetime']
start_time = datetime(d.year, d.month, d.day, 
                    d.hour, d.minute, tzinfo=timezone(params['zone']))

cbg_gluc, cbg_time, smbg_gluc, smbg_time = apply_loess(params, solution)
cbg_timesteps = make_timesteps(start_time, cbg_time)
smbg_timesteps = make_timesteps(start_time, smbg_time)

b_carbs, b_carb_timesteps, w_carbs, w_carb_timesteps, w_gluc = generate_boluses(solution, start_time)

#add settings to dfaker
settings(start_time, params)
#add basal to dfaker
scheduled_basal(start_time, params)
#add bolus values to dfaker
bolus(b_carbs, b_carb_timesteps, params)
#add wizard events to dfaker
wizard(w_gluc, w_carbs, w_carb_timesteps, params)
#add cbg values to dfaker
cbg(cbg_gluc, cbg_timesteps, params)
#add smbg values to dfaker
smbg(smbg_gluc, smbg_timesteps, params)

#write to json file
file_object = open(params['file'], mode='w')
if params['minify']: #for most compact file: separators=(',', ':')
    json.dump(dfaker, fp=file_object, sort_keys=True, separators=(',', ':'))
else:
    json.dump(dfaker, fp=file_object, sort_keys=True, indent=4) 
file_object.close()

sys.exit(0)