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

params = {
	'year' : 2015, #default datetime settings
	'month' : 1,
	'day' : 1,
	'hour' : 0,
	'minute' : 0,
	'zone' : 'US/Pacific', #default zone
	'num_days' : 30, #default days to generate data for
	'file' : 'device-data.json', #default json file name 
	'minify' : False #compact storage option false by default 
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

def get_offset(params):
	utc_tz = timezone('UTC')
	local_tz = timezone(params['zone'])
	naive = datetime(params['year'], params['month'], params['day'], params['hour'], params['minute'])
	offset = int((utc_tz.localize(naive) - local_tz.localize(naive)) / timedelta(minutes=1))
	return offset

parser = argparse.ArgumentParser()
parser.add_argument('-tz', '--timezone', dest='zone', help='Local timezone')
parser.add_argument('-d', '--date', dest='date', help='Date in the following format: YYYY-MM-DD')
parser.add_argument('-t', '--time', dest='time', help='Time in the following format: HH:MM')
parser.add_argument('-nd', '--num_days', dest='num_days',
					help='Number of days to generate data. Default = 180')
parser.add_argument('-f', '--output_file', dest='file', help='Name of output json file')
parser.add_argument('-m', '--minify', dest='minify', action='store_true', help='Minify the json file')

args = parser.parse_args()
parse(args, params)


def apply_loess(params):
	"""Solves the blood glucose equation over specified period of days 
		and applies a loess smoothing regression to the data  
	"""
	#solving blood glucose eqn 
	solution = cbg_equation.stitch_func(params['num_days'])
	glucose = solution[:, 1]
	time = solution[:, 2]
	#smoothing blood glucose eqn
	lowess = sm.nonparametric.lowess
	smoothing_distance = 1.3 #1.3 minutes
	fraction = (smoothing_distance / (params['num_days'] * 60 * 24)) * 100
	result = lowess(glucose, time, frac=fraction, is_sorted=True)
	smoothed_glucose = result[:, 1]
	smoothed_time = result[:, 0]
	return smoothed_glucose, smoothed_time

def convert_to_mmol(iterable):
	conversion_factor = 18.01559
	return [reading / conversion_factor for reading in iterable]

glucose, t = apply_loess(params)
glucose_mmol = convert_to_mmol(glucose)
offset = get_offset(params)

timesteps = []
start_timestamp = datetime(params['year'], params['month'], params['day'], 
					params['hour'], params['minute'], tzinfo=timezone(params['zone']))
epoch_ts = start_timestamp.strftime('%s')
for time_item in t:
	new_time = int(epoch_ts) + int(time_item * 60) 
	timesteps.append(new_time)

cbg_list = []
for value, timestamp in zip(glucose_mmol, timesteps):
	cbg_readings = {}
	cbg_readings["deviceId"] = "MiniMed 530G - 551-=-53875424"
	cbg_readings["id"] = str(uuid.uuid4())
	cbg_readings["uploadId"] = "upid_fdbde582fe2b"
	cbg_readings["type"] = "cbg"
	cbg_readings["value"] = value
	cbg_readings["deviceTime"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp))
	cbg_readings["timezoneOffset"] = offset 
	cbg_readings["time"] = (time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp 
							+ cbg_readings["timezoneOffset"]*60)))
	cbg_readings["units"] = "mmol/L"
	cbg_list.append(cbg_readings)

#write to json file
file_object = open(params['file'], mode='w')
if params['minify']: #for most compact file: separators=(',', ':')
	json.dump(cbg_list, fp=file_object, sort_keys=True, separators=(',', ':'))
else:
	json.dump(cbg_list, fp=file_object, sort_keys=True, indent=4) 
file_object.close()

sys.exit(0)



