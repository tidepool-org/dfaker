from chai import Chai

from dfaker.device_event import (make_alarm_event,
                                 make_status_event)


class TestMakeAlarmEvent(Chai):
    def test_fields(self):
        timestamp = 1
        zone_name = 'US/Pacific'
        alarm = make_alarm_event(timestamp, zone_name)
        self.assert_equals(alarm['type'], 'deviceEvent')


class TestMakeStatusEvent(Chai):
    def test_fields(self):
        timestamp = 1
        zone_name = 'US/Pacific'
        status = 'suspend'
        status_event = make_status_event(status, timestamp, zone_name)
        self.assert_equals(status_event['type'], 'deviceEvent')

    def test_suspend(self):
        timestamp = 1
        zone_name = 'US/Pacific'
        status = 'suspend'
        event = make_status_event(status, timestamp, zone_name)

        self.assert_equals(event['type'], 'deviceEvent')
        self.assert_equals(event['subType'], 'status')
        self.assert_equals(event['status'], 'suspended')
        self.assert_equals(event['reason'], {'suspended': 'manual'})
        self.assert_true(event['duration'] in range(3600000, 14400000,
                                                    1800000))

    def test_resume(self):
        timestamp = 1
        zone_name = 'US/Pacific'
        status = 'resume'
        event = make_status_event(status, timestamp, zone_name)
        self.assert_equals(event['type'], 'deviceEvent')
        self.assert_equals(event['subType'], 'status')
        self.assert_equals(event['status'], 'resumed')
        self.assert_equals(event['reason'], {'resumed': 'manual'})
