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
	'year' : 2015, #default datetime settings
	'month' : 1,
	'day' : 1,
	'hour' : 0,
	'minute' : 0,
	'zone' : 'US/Pacific', #default zone
	'num_days' : 30, #default days to generate data for
	'file' : 'device-data.json', #default json file name 
	'minify' : False, #compact storage option false by default 
	'gaps' : False, #randomized gaps in data, off by default 
	'smbg_freq' : 6 #default fingersticks per day
}

def parse(args, params):
	if args.date:
		try:
			params['year'] = int(args.date[0:4])
			params['month'] = int(args.date[5:7]) 
			params['day'] = int(args.date[8:])
		
			if (params['month'] not in range(1, 13) 
					or params['day'] not in range(1, 32) 
					or params['year'] not in range(1900, 2100) 
					or len(args.date) != 10):
				print('Invalid range: {:s}. Please enter date as YYYY-MM-DD'.format(args.date))
				sys.exit(1)
		except:		
			print('Wrong date format: {:s}. Please enter date as YYYY-MM-DD'.format(args.date))
			sys.exit(1)

	if args.time:
		try:
			params['hour'] = int(args.time[:2])
			params['minute'] = int(args.time[3:])

			if (params['hour'] not in range(0, 25) 
					or params['minute'] not in range(0, 61) 
					or len(args.time) != 5):
				print('Invalid range: {:s}. Please enter time as HH:MM'.format(args.time))
				sys.exit(1)
		except:
			print('Wrong time format: {:s}. Please enter time as HH:MM'.format(args.time))
			sys.exit(1)
	 
	if args.zone:
		if args.zone not in pytz.common_timezones:
			print('Unrecongznied zone: {:s}'.format(args.zone))
			sys.exit(1)
		params['zone'] = args.zone

	if args.num_days:
		params['num_days'] = args.num_days

	if args.file:
		if args.file[-5:] != '.json':
			print('Output file must be in be a json file')
			sys.exit(1)
		params['file'] = args.file

	if args.minify:
		params['minify'] = True

	if args.gaps:
		params['gaps'] = True

	if args.smbg_freq:
		if smbg_freq == 'high':
			params['smbg_freq'] = 8
		elif smbg_freq == 'average':
			params['smbg_freq'] = 6
		elif smbg_freq == 'low':
			params['smbg_freq'] = 3
		else:
			print('Invalid frequency: {:s}. Please choose between high, average and low'.format(args.smbg_freq))
			sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument('-tz', '--timezone', dest='zone', help='Local timezone')
parser.add_argument('-d', '--date', dest='date', help='Date in the following format: YYYY-MM-DD')
parser.add_argument('-t', '--time', dest='time', help='Time in the following format: HH:MM')
parser.add_argument('-nd', '--num_days', dest='num_days',
					help='Number of days to generate data. Default = 180')
parser.add_argument('-f', '--output_file', dest='file', help='Name of output json file')
parser.add_argument('-m', '--minify', dest='minify', action='store_true', help='Minify the json file')
parser.add_argument('-g', '--gaps', dest='gaps', action='store_true', help='Add gaps to fake data')
parser.add_argument('-s', '--smbg', dest='smbg_freq', help='Freqency of fingersticks a day: high, average or low')
args = parser.parse_args()
parse(args, params)

def apply_loess(params, solution):
	"""Solves the blood glucose equation over specified period of days 
		and applies a loess smoothing regression to the data 
		Returns a numpy array of glucose time values 
	"""
	#solving blood glucose eqn 
	glucose = solution[:, 1]
	time = solution[:, 2]
	#smoothing blood glucose eqn
	lowess = sm.nonparametric.lowess
	smoothing_distance = 1.3 #1.3 minutes
	fraction = (smoothing_distance / (params['num_days'] * 60 * 24)) * 100
	result = lowess(glucose, time, frac=fraction, is_sorted=True)
	
	if params['gaps']:
		result = make_gaps(params, result)
	smoothed_time = result[:, 0]
	smoothed_glucose = result[:, 1]
	return smoothed_glucose, smoothed_time

def get_offset(params):
	utc_tz = timezone('UTC')
	local_tz = timezone(params['zone'])
	naive = datetime(params['year'], params['month'], params['day'], params['hour'], params['minute'])
	offset = int((utc_tz.localize(naive) - local_tz.localize(naive)) / timedelta(minutes=1))
	return offset

def make_gaps(params, time_gluc):
	gaps = random.randint(4 * params['num_days'], 5 * params['num_days']) # amount of gaps	
	for _ in range(gaps):
		gap_length = random.randint(6, 36) # length of gaps in 5-min segments
		start_index = random.randint(0, len(time_gluc))	
		if start_index + gap_length > len(time_gluc):
			end_index = len(time_gluc) - 5
		else:
			end_index = start_index + gap_length
		time_gluc = np.delete(time_gluc, time_gluc[start_index:end_index][::2], 0)
	return time_gluc

def generate_boluses(solution, start_time):
	""" Generates events for both bolus enteries and wizard enteries.
		Returns carb, time and glucose values for each event
	"""
	all_carbs = solution[:, 0]
	glucose = solution[:,1]
	time = solution[:, 2]
	ts = make_timesteps(start_time, solution[:,2])
	positives = []
	for row in zip(all_carbs, ts, glucose):
		if row[0] > 10:
			positives.append(row)
	np_pos = np.array(clean_up_boluses(positives))
	cleaned = remove_night_boluses(np_pos)
	for row in cleaned:
		if row[0] > 120:
			row[0] = row[0] / 2	
		elif row[0] > 30:
			row[0] = row[0] * 0.75
	bolus, wizard = bolus_or_wizard(cleaned)
	np_bolus, np_wizard = np.array(bolus), np.array(wizard)
	b_carbs, b_ts  = np_bolus[:, 0], np_bolus[:, 1]
	w_card, w_ts, w_gluc = np_wizard[:, 0], np_wizard[:, 1], np_wizard[:,2]
	return b_carbs, b_ts, w_card, w_ts, w_gluc

def clean_up_boluses(carb_time, filter_rate=7):
	""" Cleans up clusters of carb events based on meal freqeuncy
		carb_time -- a numpy array of carbohydrates at different points in time
		filter_rate -- how many 5 minute segments should be filtered within the range
					   of a single event.
					   Example: 7 * 5 --> remove the next 35 minutes of data from carb_time
	"""
	return carb_time[::filter_rate]

def remove_night_boluses(carb_time_gluc):
	"""Removes night boluses excpet for events with high glucose""" 
	keep = []
	for row in carb_time_gluc:
		hour = time.gmtime(row[1]).tm_hour
		if (hour > 6 and hour < 23):
			keep.append(row)
		elif int(row[2]) not in range(0,250):
			keep.append(row)
	np_keep = np.array(keep)
	return np_keep

def bolus_or_wizard(solution):
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
	return [reading / conversion_factor for reading in iterable]

def make_timesteps(start_timestamp, timelist):
	""" Convert list of floats representing time into epoch time"""
	timesteps = []
	epoch_ts = start_timestamp.strftime('%s')
	for time_item in timelist:
		new_time = int(epoch_ts) + int(time_item * 60) 
		timesteps.append(new_time)
	return timesteps

def cbg(gluc, timesteps, params):
	for value, timestamp in zip(convert_to_mmol(gluc), timesteps):
		cbg_reading = {}
		cbg_reading["deviceId"] = "MiniMed 530G - 551-=-53875424"
		cbg_reading["id"] = str(uuid.uuid4())
		cbg_reading["uploadId"] = "upid_fdbde582fe2b"
		cbg_reading["type"] = "cbg"
		cbg_reading["value"] = value
		cbg_reading["deviceTime"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp))
		cbg_reading["timezoneOffset"] = get_offset(params)
		cbg_reading["time"] = (time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp 
								- cbg_reading["timezoneOffset"]*60)))
		cbg_reading["units"] = "mmol/L"
		dfaker.append(cbg_reading)

def smbg(gluc, timesteps, params):
	fingersticks_per_day = params['smbg_freq']
	total = (24 * 60) / 5
	increment = int(total / fingersticks_per_day)
	time_gluc = list(zip(convert_to_mmol(gluc), timesteps))
	for value, timestamp in time_gluc[::increment]:
		smbg_reading = {}
		smbg_reading["deviceId"] = "MiniMed 530G - 551-=-53875424"
		smbg_reading["id"] = str(uuid.uuid4())
		smbg_reading["type"] = "smbg"
		smbg_reading["uploadId"] = "upid_fdbde582fe2b"
		smbg_reading["value"] = value + random.uniform(-1.5, 1.5) #in mmol/L
		randimize_time = random.randint(-6000, 6000)
		smbg_reading["deviceTime"] = (time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp 
									 + randimize_time)))
		smbg_reading["timezoneOffset"] = get_offset(params) 
		smbg_reading["time"] = (time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp                          
								+ randimize_time - smbg_reading["timezoneOffset"]*60)))
		smbg_reading["units"] = "mmol/L"
		dfaker.append(smbg_reading)

def bolus(carbs, timesteps, params):
	for value, timestamp in zip(carbs, timesteps):		
		normal_or_square = random.randint(0, 4)
		if normal_or_square == 3:
			dual_square_bolus(value, timestamp, params)
		else:
			normal_bolus(value, timestamp, params)

def dual_square_bolus(value, timestamp, params):
	bolus_entry = {}
	bolus_entry["deviceId"] = "MiniMed 530G - 551-=-53875424"
	bolus_entry["id"] = str(uuid.uuid4())
	bolus_entry["uploadId"] = "upid_fdbde582fe2b"
	bolus_entry["type"] = "bolus"
	bolus_entry["subType"] = "dual/square"
	bolus_entry["normal"] = random.uniform((value / 10) / 3, (value / 10) / 2) 
	bolus_entry["extended"] = (value / 10) - bolus_entry["normal"]
	bolus_entry["duration"] = random.randrange(1800000, 5400000, 300000) #in ms
	bolus_entry["deviceTime"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp))
	bolus_entry["timezoneOffset"] = get_offset(params)
	bolus_entry["time"] = (time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp 
							- bolus_entry["timezoneOffset"]*60)))
	dfaker.append(bolus_entry)
	return bolus_entry

def normal_bolus(value, timestamp, params):
	bolus_entry = {}
	bolus_entry["deviceId"] = "MiniMed 530G - 551-=-53875424"
	bolus_entry["id"] = str(uuid.uuid4())
	bolus_entry["uploadId"] = "upid_fdbde582fe2b"
	bolus_entry["type"] = "bolus"
	bolus_entry["subType"] = "normal"
	bolus_entry["normal"] = value / 10
	bolus_entry["deviceTime"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp))
	bolus_entry["timezoneOffset"] = get_offset(params)
	bolus_entry["time"] = (time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp 
							- bolus_entry["timezoneOffset"]*60)))
	dfaker.append(bolus_entry)
	return bolus_entry

def wizard(gluc, carbs, timesteps, params):
	access_settings = dfaker[0]
	for gluc_val, carb_val, timestamp in zip(gluc, carbs, timesteps):
		wizard_reading = {}
		wizard_reading["type"] = "wizard"
		wizard_reading["bgInput"] = gluc_val
		wizard_reading["carbInput"] = int(carb_val)
		wizard_reading["insulinOnBoard"] = 0
		wizard_reading["insulinCarbRatio"] = access_settings["carbRatio"][0]["amount"]
		wizard_reading["insulinSensitivity"] = access_settings["insulinSensitivity"][0]["amount"]
		wizard_reading["bgTarget"] = { "high": access_settings["bgTarget"][0]["high"],
            							"low": access_settings["bgTarget"][0]["low"]}
		wizard_reading["payload"] = {}
		wizard_reading["recommended"] = {}
		wizard_reading["recommended"]["carb"] = wizard_reading["carbInput"] / wizard_reading["insulinCarbRatio"]
		wizard_reading["recommended"]["correction"] =  0
		wizard_reading["recommended"]["net"] = (wizard_reading["recommended"]["carb"] 
											   + wizard_reading["recommended"]["correction"] - wizard_reading["insulinOnBoard"])
		normal_or_square = random.randint(0, 4)
		if normal_or_square == 3:
			bolus = dual_square_bolus
		else:
			bolus = normal_bolus
		wizard_reading["bolus"] = bolus(carb_val, timestamp, params)["id"]

		wizard_reading["deviceId"] = "MiniMed 530G - 551-=-53875424"
		wizard_reading["uploadId"] = "upid_fdbde582fe2b"
		wizard_reading["id"] = str(uuid.uuid4())
		wizard_reading["deviceTime"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp))
		wizard_reading["timezoneOffset"] = get_offset(params)
		wizard_reading["time"] = (time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp 
								  - wizard_reading["timezoneOffset"]*60)))
		dfaker.append(wizard_reading)

def settings(start_time, params):
	settings = {}
	settings["activeSchedule"] = "standard"
	settings["basalSchedules"] =  {"standard": [{"rate": 0.75, "start": 0},
												{"rate": 0.6, "start": 3600000},
												{"rate": 0.65, "start": 10800000},
												{"rate": 0.8, "start": 14400000},
												{"rate": 0.85, "start": 18000000},
												{"rate": 0.8, "start": 28800000},
												{"rate": 0.75, "start": 32400000},
												{"rate": 0.8, "start": 54000000},
												{"rate": 0.85, "start": 61200000}]}
	settings["bgTarget"] = [{"high": random.uniform(5.8, 6.2), 
							 "low": random.uniform(4.4, 5.2), 
							 "start": 0}]
	settings["carbRatio"] = [ {"amount": random.randint(9, 15), "start": 0}]
	settings["insulinSensitivity"] = [{"amount": 2.7, "start": 0}]
	settings["type"] = "settings"
	settings["units"] = { "bg": "mg/dL","carb": "grams"}
	settings["deviceId"] = "MiniMed 530G - 551-=-53875424"
	settings["uploadId"] = "upid_fdbde582fe2b"
	settings["id"] = str(uuid.uuid4())
	time_in_seconds = int(start_time.strftime('%s'))
	settings["deviceTime"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(time_in_seconds))
	settings["timezoneOffset"] = get_offset(params)
	settings["time"] = (time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time_in_seconds
							  - settings["timezoneOffset"]*60)))
	dfaker.append(settings)

dfaker = [] 
solution = cbg_equation.stitch_func(params['num_days'])

start_time = datetime(params['year'], params['month'], params['day'], 
					params['hour'], params['minute'], tzinfo=timezone(params['zone']))

glucose, gluc_time = apply_loess(params, solution)
gluc_timesteps = make_timesteps(start_time, gluc_time)

b_carbs, b_carb_timesteps, w_carbs, w_carb_timesteps, w_gluc = generate_boluses(solution, start_time)


#add settings to dfaker
settings(start_time, params)
#add bolus values to dfaker
bolus(b_carbs, b_carb_timesteps, params)
#add wizard events to dfaker
wizard(w_gluc, w_carbs, w_carb_timesteps, params)
#add cbg values to dfaker
cbg(glucose, gluc_timesteps, params)
#add smbg values to dfaker
smbg(glucose, gluc_timesteps, params)


#write to json file
file_object = open(params['file'], mode='w')
if params['minify']: #for most compact file: separators=(',', ':')
	json.dump(dfaker, fp=file_object, sort_keys=True, separators=(',', ':'))
else:
	json.dump(dfaker, fp=file_object, sort_keys=True, indent=4) 
file_object.close()

sys.exit(0)



