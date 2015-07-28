import random

from . import common_fields

def device_meta(subType, timestamp, zonename, time_before_change, time_after_change, new_zone):
    """Create a device meta event based on the subType specified"""
    if subType == "status":
        meta_entry, duration = status(timestamp, zonename)
        return meta_entry, duration
    elif subType == "timeChange":
        meta_entry = time_change(timestamp, zonename, time_before_change, time_after_change, new_zone)
        return meta_entry

def time_change(timestamp, zonename, time_before_change, time_after_change, new_zone):
    """ Generate a time change meta event for traveling purposes"""
    meta_entry = {}
    meta_entry = common_fields.add_common_fields('deviceMeta', meta_entry, timestamp, zonename)
    meta_entry["change"] = {}
    meta_entry["change"]["agent"] = "manual"
    meta_entry["change"]["from"] = str(time_before_change)[:10] + 'T' + str(time_before_change)[11:]
    meta_entry["change"]["to"] = str(time_after_change)[:10] + 'T' + str(time_after_change)[11:]
    meta_entry["change"]["timezone"] = new_zone
    meta_entry["reasons"] = "travel"
    meta_entry["subType"] = "timeChange"
    return meta_entry

def status(timestamp, zonename):
    """ Generate a statys meta event to suspend pump"""
    meta_entry = {}
    meta_entry = common_fields.add_common_fields('deviceMeta', meta_entry, timestamp, zonename)
    meta_entry["subType"] = "status"
    meta_entry["duration"] = random.randrange(3600000, 14400000, 1800000)
    meta_entry["status"] = "suspended"  
    return meta_entry, meta_entry["duration"]

def suspend_pump():
    decision = random.randint(0,49) #for 1 in 50 instances, the pump will be suspended 
    if decision == 2:
        return True
    return False