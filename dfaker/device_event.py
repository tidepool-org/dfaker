import random

from . import common_fields


class Constants:
    FIELD_NAME = 'deviceEvent'


def make_time_change_event(timestamp, zonename, time_before_change,
                           time_after_change, new_zone):
    """ Generate a time change event for traveling purposes"""
    event = {}
    event = common_fields.add_common_fields(Constants.FIELD_NAME, event,
                                            timestamp, zonename)
    event["change"] = {}
    event["change"]["agent"] = "manual"
    event["change"]["from"] = \
        str(time_before_change)[:10] + 'T' + str(time_before_change)[11:]
    event["change"]["to"] = \
        str(time_after_change)[:10] + 'T' + str(time_after_change)[11:]
    event["change"]["timezone"] = new_zone
    event["reasons"] = "travel"
    event["subType"] = "timeChange"
    return event


def make_alarm_event(timestamp, zonename):
    """ Generate an alarm device event"""
    event = {}
    event = common_fields.add_common_fields(Constants.FIELD_NAME, event,
                                            timestamp, zonename)
    event["subType"] = "alarm"
    event["alarmType"] = "low_insulin"
    return event


def make_status_event(status, timestamp, zone_name):
    """ Generate a status event"""
    event = {}
    event = common_fields.add_common_fields(Constants.FIELD_NAME, event,
                                            timestamp, zone_name)
    event["subType"] = "status"
    if status == 'suspend':
        event["status"] = "suspended"
        event["reason"] = {
            "suspended": "manual"
        }
        event["duration"] = random.randrange(3600000, 14400000, 1800000)
    elif status == 'resume':
        event["status"] = "resumed"
        event["reason"] = {
            "resumed": "manual"
        }
    return event


def suspend_pump():
    # for 1 in 50 instances, the pump will be suspended
    decision = random.randint(0, 49)
    if decision == 2:
        return True
    return False
