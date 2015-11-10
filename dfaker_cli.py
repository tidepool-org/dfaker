# usage: dfaker_cli.py [-h] [-z ZONE] [-d DATE] [-t TIME] [-n NUM_DAYS]
#                      [-f FILE] [-m] [-g] [-s SMBG_FREQ] [-r] [-p PUMP]
#
# optional arguments:
#  -h,           --help               show this help message and exit
#  -z ZONE,      --timezone ZONE      Local timezone
#  -d DATE,      --date DATE          Date in the following format: YYYY-MM-DD
#  -t TIME,      --time TIME          Time in the following format: HH:MM
#  -n NUM_DAYS,  --num_days NUM_DAYS  Number of days to generate data
#  -f FILE,      --output_file FILE   Name of output json file
#  -m,           --minify             Minify the json file
#  -g,           --gaps               Add gaps to fake data
#  -s SMBG_FREQ, --smbg SMBG_FREQ     Freqency of fingersticks a day: high,
#                                     average or low
#  -r,           --travel             Add travel option
#  -p PUMP,      --pump PUMP          Specify pump name

from datetime import datetime
import pytz
import json
import argparse
import sys

from dfaker.data_generator import dfaker
from dfaker.travel import travel


def parse(args, params):
    if args.date:
        try:
            d = datetime.strptime(args.date, '%Y-%m-%d')
            year, month, day = d.year, d.month, d.day
            params['datetime'] = params['datetime'].replace(year=year,
                                                            month=month,
                                                            day=day)
        except:
            print('Wrong date format: {:s}. Please enter date as YYYY-MM-DD'
                  .format(args.date))
            sys.exit(1)

    if args.time:
        try:
            t = datetime.strptime(args.time, '%H:%M')
            hour, minute = t.hour, t.minute
            params['datetime'] = params['datetime'].replace(hour=hour,
                                                            minute=minute)

        except:
            print(('Wrong time format: {:s}. Please enter time as HH:MM')
                  .format(args.time))
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
            print('Invalid frequency: {:s}. Please choose between high, '
                  'average and low'.format(args.smbg_freq))
            sys.exit(1)

    if args.travel:
        params['travel'] = True

    if args.pump:
        if args.pump == 'OmniPod':
            params['pump_name'] = 'OmniPod'
        elif args.pump == 'Tandem':
            params['pump_name'] = 'Tandem'
        elif args.pump == 'Medtronic':
            params['pump_name'] = 'Medtronic'
        else:
            print('Invalid pump name. Current options include: OmniPod, '
                  'Tandem or Medtronic.')
            sys.exit(1)

    if not args.pump:
        print("Prefered pump name not entered, revert to default pump: "
              "Medtronic")

    return params


def main():
    params = {
        'datetime': datetime.strptime('2015-01-01 00:00', '%Y-%m-%d %H:%M'),
        'zone': 'US/Pacific',
        'num_days': 180,
        'file': 'device-data.json',
        'minify': False,
        'gaps': False,  # randomized gaps in data, off by default
        'smbg_freq': 6,  # default number of fingersticks per day
        'travel': False,
        'pump_name': 'Medtronic'
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('-z', '--timezone', dest='zone', help='Local timezone')
    parser.add_argument('-d', '--date', dest='date',
                        help='Date in the following format: YYYY-MM-DD')
    parser.add_argument('-t', '--time', dest='time',
                        help='Time in the following format: HH:MM')
    parser.add_argument('-n', '--num_days', dest='num_days',
                        help='Number of days to generate data')
    parser.add_argument('-f', '--output_file', dest='file',
                        help='Name of output json file')
    parser.add_argument('-m', '--minify', dest='minify', action='store_true',
                        help='Minify the json file')
    parser.add_argument('-g', '--gaps', dest='gaps', action='store_true',
                        help='Add gaps to fake data')
    parser.add_argument('-s', '--smbg', dest='smbg_freq',
                        help='Freqency of fingersticks a day: high, average '
                        'or low')
    parser.add_argument('-r', '--travel', dest='travel', action='store_true',
                        help='Add travel option')
    parser.add_argument('-p', '--pump', dest='pump', help='Specify pump name')
    args = parser.parse_args()
    params = parse(args, params)

    # if travelling occurs during simulation, generate data in multiple
    # timezones
    if params['travel']:
        result = (travel(params['num_days'], params['datetime'],
                  params['zone'], params['gaps'], params['smbg_freq'],
                  params['pump_name']))
    # if not travelling, generate data within a single timezone
    else:
        result = (dfaker(params['num_days'], params['zone'],
                  params['datetime'], params['gaps'], params['smbg_freq'],
                  params['pump_name']))

    # write to json file
    file_object = open(params['file'], mode='w')
    if params['minify']:  # for most compact file: separators=(',', ':')
        json.dump(result, fp=file_object, sort_keys=True,
                  separators=(',', ':'))
    else:
        json.dump(result, fp=file_object, sort_keys=True,
                  indent=4)
    file_object.close()

    sys.exit(0)


if __name__ == '__main__':
    main()
