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

from datetime import datetime
import pytz
import json
import argparse 
import sys
import bg_simulator
from bolus import bolus, generate_boluses
from wizard import wizard
from settings import settings
from cbg import cbg, apply_loess
from smbg import smbg
from basal import scheduled_basal
import tools

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

def main():
    params = {
        'datetime' : datetime.strptime('2015-03-03 0:0', '%Y-%m-%d %H:%M'), #default datetime settings
        'zone' : 'US/Pacific', #default zone
        'num_days' : 10, #default number of days to generate data for
        'file' : 'device-data.json', #default json file name 
        'minify' : False, #compact storage option false by default 
        'gaps' : False, #randomized gaps in data, off by default 
        'smbg_freq' : 6 #default number of fingersticks per day
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
    args = parser.parse_args()
    parse(args, params)

    dfaker = [] 
    solution = bg_simulator.simulate(params['num_days'])

    d = params['datetime']
    start_time = datetime(d.year, d.month, d.day, 
                        d.hour, d.minute, tzinfo=pytz.timezone(params['zone']))

    cbg_gluc, cbg_time, smbg_gluc, smbg_time = apply_loess(solution, num_days=params['num_days'], gaps=params['gaps'])
    cbg_timesteps = tools.make_timesteps(start_time, cbg_time)
    smbg_timesteps = tools.make_timesteps(start_time, smbg_time)

    b_carbs, b_carb_timesteps, w_carbs, w_carb_timesteps, w_gluc = generate_boluses(solution, start_time)

    #make settings 
    settings_data = settings(start_time, zonename=params['zone'])
    #make basal values
    basal_data, pump_suspended = scheduled_basal(start_time, num_days=params['num_days'], zonename=params['zone'])
    #make bolus values 
    bolus_data = bolus(start_time, b_carbs, b_carb_timesteps, no_bolus=pump_suspended, zonename=params['zone'])
    #make wizard events
    wizard_data = (wizard(start_time, w_gluc, w_carbs, w_carb_timesteps, basal_data=basal_data,
                         no_wizard=pump_suspended, zonename=params['zone']))
    #make cbg values 
    cbg_data = cbg(cbg_gluc, cbg_timesteps, zonename=params['zone'])
    #make smbg values 
    smbg_data = smbg(smbg_gluc, smbg_timesteps, stick_freq=params['smbg_freq'], zonename=params['zone'])

    dfaker = dfaker + settings_data + basal_data + bolus_data + wizard_data + cbg_data + smbg_data

    #write to json file
    file_object = open(params['file'], mode='w')
    if params['minify']: #for most compact file: separators=(',', ':')
        json.dump(dfaker, fp=file_object, sort_keys=True, separators=(',', ':'))
    else:
        json.dump(dfaker, fp=file_object, sort_keys=True, indent=4) 
    file_object.close()

if __name__ == '__main__':
    main()

sys.exit(0)