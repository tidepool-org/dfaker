from . import tools
import math
import random
from datetime import timedelta
from .data_generator import dfaker

def travel(num_days, start_date, curr_zone, gaps, smbg_freq):
    """ Arrange travel simulation over the courseo of num_days
        If num days is greater than 30, allow for multiple travel events
    """
    result = []
    if num_days <= 30: #generate only 1 travel event
        result = travel_event(num_days, start_date, curr_zone, gaps, smbg_freq)
    else:
        times_travelled = random.randint(2, math.ceil(num_days / 30))
        segment = num_days / times_travelled
        for _ in range(0, times_travelled):
            result += travel_event(segment, start_date, curr_zone, gaps, smbg_freq)
            start_date += timedelta(days=segment)
    return result

def travel_event(num_days, start_date, curr_zone, gaps, smbg_freq): 
    """ Simulate a single travel event over the course of num_days
    """
    result = []
    
    #set max travelling days according to num_days 
    if num_days / 3 < 6:
        maxDays = 6
    else:
        maxDays = int(num_days / 3)
    travel_days = random.randint(5, maxDays)
    travel_zone = select_travel_destination(curr_zone)
    travel_start_date = start_date + timedelta(days=random.randint(2, int(num_days - travel_days - 1)))

    #count number of days before and after travelling event     
    days_before = (travel_start_date - start_date).days + (travel_start_date - start_date).seconds / (60*60*24)
    days_after = num_days - days_before - travel_days
    
    offset_diff = ((tools.get_offset(travel_zone, travel_start_date) - 
                    tools.get_offset(curr_zone, travel_start_date)) / 60)
    start_travel = travel_start_date + timedelta(hours=offset_diff)
    end_travel = travel_start_date + timedelta(days=travel_days)

    #generate data for each segment
    before_travel= dfaker(days_before, curr_zone, start_date, gaps, smbg_freq)
    during_travel = dfaker(travel_days, travel_zone, start_travel, gaps, smbg_freq)
    after_travel = dfaker(days_after, curr_zone, end_travel, gaps, smbg_freq)

    result += before_travel + during_travel + after_travel
    return result

def select_travel_destination(curr_zone):
    """Select a random travel destination for each travel event"""
    possible_destinations = ['US/Pacific', 'US/Mountain', 'US/Central', 'US/Eastern', 
                            'Mexico/General', 'Australia/Sydney', 'Europe/London', 
                            'Europe/Moscow', 'Europe/Copenhagen', 'Japan', 'Singapore']
    #randomley select a destination
    random_index = random.randint(0, len(possible_destinations) - 1)
    destination = possible_destinations[random_index]
    #make sure destination does not match curr_zone
    if destination == curr_zone:
        print("enter")
        destination = select_travel_destination(curr_zone)
        #destination = possible_destinations[random_index + 1]
    return destination
