from datetime import datetime, timedelta, tzinfo
import time
from pytz import timezone
import pytz
import uuid
import json
import argparse 
import sys
import cbg_equation

params = {
	'year' : 2015, #default datetime settings
	'month' : 3,
	'day' : 8,
	'hour' : 0,
	'minute' : 0,
	'zone' : 'US/Pacific' #default zone
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

def get_offset(params):
	utc_tz = timezone('UTC')
	local_tz = timezone(params['zone'])
	naive = datetime(params['year'], params['month'], params['day'], params['hour'], params['minute'])
	offset = int((utc_tz.localize(naive) - local_tz.localize(naive)) / timedelta(minutes=1))
	return offset

parser = argparse.ArgumentParser()
parser.add_argument('--timezone', '--tz', dest='zone', help='Enter local timezone')
parser.add_argument('--date', dest='date', help='Enter date in the following format: YYYY-MM-DD')
parser.add_argument('--time', dest='time', help='Enter time in the following format: HH:MM')
args = parser.parse_args()

print(args.__dict__)

parse(args, params)

offset = get_offset(params)
print(offset)

#solving blood glucose eqn 
solution = cbg_equation.simulator()
carbs = solution[:, 0]
glucose = solution[:, 1]
t = solution[:, 2]

def convert_to_mmol(iterable):
	conversion_facgtor = 18.01559
	return [reading / conversion_facgtor for reading in iterable]

glucose_mmol = convert_to_mmol(glucose)

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
	cbg_list.append(cbg_readings)

#write to json file
file_object = open("cbg.json", mode='w')
json.dump(cbg_list, fp=file_object, sort_keys=True, separators=(',', ':'))
file_object.close()

sys.exit(0)



