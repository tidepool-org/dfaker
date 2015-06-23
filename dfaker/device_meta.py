import random

from . import common_fields

def device_meta(timestamp, zonename):
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