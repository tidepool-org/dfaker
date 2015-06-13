import random 
from datetime import datetime
import common_fields
import tools

def remove_night_smbg(gluc, timesteps):
    """ Remove most smbg night events """
    keep = []
    for row in zip(gluc, timesteps):
        hour = datetime.fromtimestamp(row[1]).hour
        night_smbg = random.randint(0, 4) #keep some random night smbg events 
        if hour > 6 and hour < 24:
            keep.append(row)
        elif night_smbg == 2:
            keep.append(row)
    return keep
        
def randomize_smbg(time_gluc, params):
    """ Randomize smbg times according to fingerstick frequency """
    fingersticks_per_day = params["smbg_freq"]
    total = (24 * 60) / 5 
    increment = int(total / fingersticks_per_day)
    start, keep = 0, []
    while start < len(time_gluc):
        try:
            index = random.randint(start, start + increment)
            keep.append(time_gluc[index])
            start += increment
        except:
            break
    return keep

def smbg(gluc, timesteps, params):
    smbg_data = []
    remove_night = remove_night_smbg(gluc, timesteps)   
    time_gluc = randomize_smbg(remove_night, params)
    for value, timestamp in time_gluc:
        randomize_time = random.randrange(-5000, 5000)
        smbg_reading = {}
        smbg_reading = common_fields.add_common_fields('smbg', smbg_reading, timestamp, params)
        smbg_reading["value"] = tools.convert_to_mmol(value) + random.uniform(-1.5, 1.5) #in mmol/L
        if value >= 600:
            smbg_reading["annotation"] = [{"code": "bg/out-of-range", "threshold": 600, "value": "high"}]
            smbg_reading["value"] = tools.convert_to_mmol(601)
        elif value <= 20:
            smbg_reading["annotation"] = [{"code": "bg/out-of-range", "threshold": 20, "value": "low"}]
            smbg_reading["value"] = tools.convert_to_mmol(19)        
        smbg_reading["units"] = "mmol/L"
        smbg_data.append(smbg_reading)
    return smbg_data