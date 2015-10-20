from datetime import datetime
import time
import uuid

from . import tools

def add_common_fields(name, datatype, timestamp, zonename):
    """ Populate common fields applicable to all datatypes
        name -- name of datatype
        datatype -- a dictionary for a specific data type
        timestamp -- an epoch time in utc
        zonename -- name of timezone in effect 
    """
    datatype["type"] = name
    datatype["deviceId"] = "DemoData-123456789"
    datatype["uploadId"] = "upid_abcdefghijklmnop"
    datatype["id"] = str(uuid.uuid4())
    datatype["timezoneOffset"] = tools.get_offset(zonename, datetime.fromtimestamp(timestamp))
    datatype["deviceTime"] = (time.strftime('%Y-%m-%dT%H:%M:%S', 
                              time.gmtime(timestamp + datatype["timezoneOffset"]*60)))
    datatype["time"] = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(timestamp))
    datatype["conversionOffset"] = 0
    return datatype
