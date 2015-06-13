from pytz import timezone

def get_offset(zone, date):
    local_tz = timezone(zone)   
    return - (24 * 60 - local_tz.utcoffset(date).seconds / 60) 

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