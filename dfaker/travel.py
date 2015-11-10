from . import tools
import math
import random
from datetime import timedelta
from .data_generator import dfaker
from .device_event import make_time_change_event


def travel(num_days, start_date, curr_zone, gaps, smbg_freq, pump_name):
    """ Arrange travel simulation over the courseo of num_days
        If num days is greater than 30, allow for multiple travel events
    """
    result = []
    if num_days <= 30:  # generate only 1 travel event
        result = travel_event(num_days, start_date, curr_zone, gaps,
                              smbg_freq, pump_name)
    else:
        times_travelled = random.randint(2, math.ceil(num_days / 30))
        segment = num_days / times_travelled
        for _ in range(0, times_travelled):
            result += travel_event(segment, start_date, curr_zone, gaps,
                                   smbg_freq, pump_name)
            start_date += timedelta(days=segment)
    return result


def travel_event(num_days, start_date, curr_zone, gaps, smbg_freq, pump_name):
    """ Simulate a single travel event over the course of num_days
    """
    result = []

    # set max travelling days according to num_days
    if num_days / 3 < 6:
        maxDays = 6
    else:
        maxDays = int(num_days / 3)
    travel_days = random.randint(5, maxDays)
    travel_zone = select_travel_destination(curr_zone)
    rand_int = random.randint(2, int(num_days - travel_days - 1))
    travel_start_date = start_date + timedelta(days=rand_int)

    # count number of days before and after travelling event
    days_before = ((travel_start_date - start_date).days +
                   (travel_start_date - start_date).seconds / (60*60*24))
    days_after = num_days - days_before - travel_days

    curr_zone_offset = tools.get_offset(travel_zone, travel_start_date)
    new_zone_offset = tools.get_offset(curr_zone, travel_start_date)
    offset_diff = (new_zone_offset - curr_zone_offset) / 60
    start_travel = travel_start_date + timedelta(hours=offset_diff)

    end_travel = travel_start_date + timedelta(days=travel_days)

    # generate data for each segment
    before_travel = dfaker(days_before, curr_zone, start_date, gaps, smbg_freq,
                           pump_name)
    during_travel = dfaker(travel_days, travel_zone, start_travel, gaps,
                           smbg_freq, pump_name)
    after_travel = dfaker(days_after, curr_zone, end_travel, gaps, smbg_freq,
                          pump_name)

    # add device meta event for each timechange
    timestamp = tools.convert_ISO_to_epoch(
        str(travel_start_date - timedelta(minutes=curr_zone_offset)),
        '%Y-%m-%d %H:%M:%S')
    time_change_meta_event = make_time_change_event(timestamp, curr_zone,
                                                    travel_start_date,
                                                    start_travel, travel_zone)
    before_travel.append(time_change_meta_event)

    timestamp = tools.convert_ISO_to_epoch(
        str(end_travel - timedelta(minutes=new_zone_offset)),
        '%Y-%m-%d %H:%M:%S')
    end_travel_in_timezone = start_travel + timedelta(days=travel_days)
    time_change_meta_event = make_time_change_event(
        timestamp, travel_zone, end_travel_in_timezone, end_travel, curr_zone)
    during_travel.append(time_change_meta_event)

    result += before_travel + during_travel + after_travel
    return result


def select_travel_destination(curr_zone):
    """Select a random travel destination for each travel event"""
    possible_destinations = ['US/Pacific', 'US/Mountain', 'US/Central',
                             'US/Eastern', 'Mexico/General',
                             'Australia/Sydney', 'Europe/London',
                             'Europe/Moscow', 'Europe/Copenhagen',
                             'Japan', 'Singapore']
    # randomley select a destination
    random_index = random.randint(0, len(possible_destinations) - 1)
    destination = possible_destinations[random_index]
    # make sure destination does not match curr_zone
    if destination == curr_zone:
        destination = select_travel_destination(curr_zone)
    return destination
