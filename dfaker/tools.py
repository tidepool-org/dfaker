import pytz
from datetime import datetime, timedelta


def is_dst(zonename, date):
    local_tz = pytz.timezone(zonename)
    localized_time = local_tz.localize(date)
    return localized_time.dst() != timedelta(0)


def get_offset(zonename, date):
    local_tz = pytz.timezone(zonename)
    if zonename == 'UTC':
        return 0
    elif is_dst(zonename, date):
        return local_tz.utcoffset(date, is_dst=True).total_seconds() / 60
    else:
        return local_tz.utcoffset(date, is_dst=False).total_seconds() / 60


def convert_to_mmol(iterable):
    conversion_factor = 18.01559
    if isinstance(iterable, float) or isinstance(iterable, int):
        return iterable / conversion_factor
    return [reading / conversion_factor for reading in iterable]


def round_to(n, precision=0.005):
    """ The round function can take positive or negative values
        and round them to a certain precision.
        In the fake data generator, only positive values are being passed
        into it
    """
    if n >= 0:
        correction = 0.5
    else:
        correction = -0.5
    result = int(n / precision + correction) * precision
    return round(result, 3)


def make_timesteps(start_time, offset, timelist):
    """ Convert list of floats representing time into epoch time
        start_time -- a timezone naive datetime object
        offset -- offset in minutes
        timelist -- a list of incrementing floats representing time increments
    """
    timesteps = []
    epoch_ts = convert_ISO_to_epoch(str(start_time), '%Y-%m-%d %H:%M:%S')
    local_timestamp = epoch_ts - offset*60
    for time_item in timelist:
        new_time = int(local_timestamp) + int(time_item * 60)
        timesteps.append(new_time)
    return timesteps


def convert_ISO_to_epoch(datetime_string, date_format):
    """ Takes a datetime string and returns an epoch time in seconds
        Only works when datetime_string is in UTC
    """
    datetime_object = datetime.strptime(datetime_string, date_format)
    epoch = datetime.utcfromtimestamp(0)
    delta = datetime_object - epoch
    return int(delta.total_seconds())


def get_rate_from_settings(schedule, time, name):
    """Obtains a rate or amount from settings based on time of day
       If name is basalSchedules, returns rate as well as start and stop times
       Otherwise, if name is carbRatio or insulinSensitivity, returns just
       amount
       Returned results are in mmol/L.
    """
    t = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S')
    if name == "basalSchedules":  # account for variation in naming
        value_name = "rate"  # set initial rate
    else:
        value_name = "amount"
    ms_since_midnight = t.hour*60*60*1000 + t.minute*60*1000 + t.second*1000
    last_segment = schedule[len(schedule)-1]
    full_day = 86400000  # 24 hours in ms
    rate = schedule[0][value_name]  # set initial rate
    initial_start = ms_since_midnight  # set initial start time
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
        rate = segment[value_name]  # update rate to next segment rate
    if name == "basalSchedules":
        return rate, start, initial_start, end
    return rate  # only rate needed for insulin sensitivity/carb ratio events
