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
    local_datetime = datetime.fromtimestamp(timestamp)
    datatype["timezoneOffset"] = tools.get_offset(zonename, local_datetime)
    offset_time_seconds = datatype["timezoneOffset"] * 60
    offset_time_struct_utc = time.gmtime(timestamp + offset_time_seconds)
    datatype["deviceTime"] = time.strftime('%Y-%m-%dT%H:%M:%S',
                                           offset_time_struct_utc)
    time_struct_utc = time.gmtime(timestamp)
    datatype["time"] = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time_struct_utc)
    datatype["conversionOffset"] = 0
    return datatype
