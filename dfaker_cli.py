#usage: py [-h] [-z ZONE] [-d DATE] [-t TIME] [-n NUM_DAYS] [-f FILE]
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

from datetime import datetime, timedelta
import pytz
import json
import argparse 
import sys
from dfaker import bg_simulator
from dfaker.bolus import bolus, generate_boluses
from dfaker.wizard import wizard
from dfaker.settings import settings
from dfaker.cbg import cbg, apply_loess
from dfaker.smbg import smbg
from dfaker.basal import scheduled_basal
import dfaker.tools as tools
import random

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
            print('Wrong input, num_days argument should be an integer')
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

    if args.travel_info:
        try: #check days traveled is a positive int
            days_travelled = int(args.travel_info[0])
            if days_travelled <= 0:
               # print('Wrong input, first parameter must be a positive integer')
                sys.exit(1)
        except:
            print('Wrong input, first parameter must be a positive integer')
            sys.exit(1)
        
        try: #check proper format of start travel date
            start_travel = datetime.strptime(args.travel_info[1], '%Y-%m-%dT%H:%M')
        except:
            print('Wrong input: {:s}. second parameter must be a datetime string in the following format: YYYY-MM-DDTHH:MM'.format(args.travel_info[1]))
            sys.exit(1)

        #check validity of travel dates
        if params['datetime'] > start_travel:
            print('Invalif input: travel date entered is before start date of simulation')
            sys.exit(1)
        if params['datetime'] + timedelta(days=params['num_days']) < start_travel:
            print('Invalid input: travel date entered is after end date of simulation')
            sys.exit(1)

        #check destination timezone is a proper zone 
        destination_timezone = args.travel_info[2]
        if destination_timezone not in pytz.common_timezones:
            print('Wrong input, third parameter must be a proper timezone. Unrecognized zone: {:s}'.format(destination_timezone))
            sys.exit(1)

        #update params 
        params['travel_days'] = days_travelled
        params['travel_zone'] = destination_timezone
        params['start_travel_date'] = start_travel

    return params

def dfaker(num_days, zonename, date_time, gaps, smbg_freq):
    """ Generate data for a set num_days within a single timezone
    """
    dfaker = [] 
    solution = bg_simulator.simulate(num_days)

    start_time = datetime(date_time.year, date_time.month, date_time.day, date_time.hour, date_time.minute)
    zone_offset = tools.get_offset(zonename, start_time)

    cbg_gluc, cbg_time, smbg_gluc, smbg_time = apply_loess(solution, num_days=num_days, gaps=gaps)
    cbg_timesteps = tools.make_timesteps(start_time, zone_offset, cbg_time)
    smbg_timesteps = tools.make_timesteps(start_time, zone_offset, smbg_time)

    b_carbs, b_carb_timesteps, w_carbs, w_carb_timesteps, w_gluc = (
            generate_boluses(solution, start_time, zonename=zonename, zone_offset=zone_offset))

    #make settings 
    settings_data = settings(start_time, zonename=zonename)
    #make basal values
    basal_data, pump_suspended = scheduled_basal(start_time, num_days=num_days, zonename=zonename)
    #make bolus values 
    bolus_data = bolus(start_time, b_carbs, b_carb_timesteps, no_bolus=pump_suspended, zonename=zonename)
    #make wizard events
    wizard_data, iob_data = (wizard(start_time, w_gluc, w_carbs, w_carb_timesteps, bolus_data=bolus_data,
                         no_wizard=pump_suspended, zonename=zonename))
    #make cbg values 
    cbg_data = cbg(cbg_gluc, cbg_timesteps, zonename=zonename)
    #make smbg values 
    smbg_data = smbg(smbg_gluc, smbg_timesteps, stick_freq=smbg_freq, zonename=zonename)

    dfaker = dfaker + settings_data + basal_data + bolus_data + wizard_data + cbg_data + smbg_data
    return dfaker

def main():
    params = {
        'datetime' : datetime.strptime('2015-03-03 0:0', '%Y-%m-%d %H:%M'), #default datetime settings
        'zone' : 'US/Pacific', #default zone
        'num_days' : 10, #default number of days to generate data for
        'file' : 'device-data.json', #default json file name 
        'minify' : False, #compact storage option false by default 
        'gaps' : False, #randomized gaps in data, off by default 
        'smbg_freq' : 6, #default number of fingersticks per day
        'travel_days' : 0, #by default, no traveling occures during simulation period
        'travel_zone' : None, 
        'start_travel_date' : None
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('-z', '--timezone', dest='zone', help='Local timezone')
    parser.add_argument('-d', '--date', dest='date', help='Date in the following format: YYYY-MM-DD')
    parser.add_argument('-t', '--time', dest='time', help='Time in the following format: HH:MM')
    parser.add_argument('-n', '--num_days', dest='num_days', help='Number of days to generate data')
    parser.add_argument('-f', '--output_file', dest='file', help='Name of output json file')
    parser.add_argument('-m', '--minify', dest='minify', action='store_true', help='Minify the json file')
    parser.add_argument('-g', '--gaps', dest='gaps', action='store_true', help='Add gaps to fake data')
    parser.add_argument('-s', '--smbg', dest='smbg_freq', help='Freqency of fingersticks a day: high, average or low')
    (parser.add_argument('-r', '--travel', dest='travel_info', nargs=3,
            help='Num days traveling + space + Date and time in the following format: YYYY-MM-DDTHH:MM + space + destination timezone'))
    args = parser.parse_args()
    params = parse(args, params)

    #if travelling occurs during simulation, generate data in multiple timezones 
    if params['travel_days']:
        days_before = (params['start_travel_date'] - params['datetime']).days + (params['start_travel_date'] - params['datetime']).seconds / (60*60*24)
        days_after = params['num_days'] - days_before - params['travel_days']
        end_travel = params['start_travel_date'] + timedelta(days=params['travel_days'])
    
        before_travel= dfaker(days_before, params['zone'], params['datetime'], params['gaps'], params['smbg_freq'])
        during_travel = dfaker(params['travel_days'], params['travel_zone'], params['start_travel_date'], params['gaps'], params['smbg_freq'])
        after_travel = dfaker(days_after, params['zone'], end_travel, params['gaps'], params['smbg_freq'])
    
        result = before_travel + during_travel + after_travel
        
    #if not travelling, generate data within a single timezone
    else:
        result = dfaker(params['num_days'], params['zone'], params['datetime'], params['gaps'], params['smbg_freq'])

    #write to json file
    file_object = open(params['file'], mode='w')
    if params['minify']: #for most compact file: separators=(',', ':')
        json.dump(result, fp=file_object, sort_keys=True, separators=(',', ':'))
    else:
        json.dump(result, fp=file_object, sort_keys=True, indent=4) 
    file_object.close()

    sys.exit(0)

if __name__ == '__main__':
    main()