from chai import Chai
from datetime import datetime

from dfaker.pump_settings import make_pump_settings


class Test_Pump_Settings(Chai):
    def test_type(self):
        start_time = datetime(2015, 1, 1, 0, 0, 0)
        zone_name = 'US/Pacific'
        pump_name = 'Medtronic'
        settings_list = make_pump_settings(start_time, zone_name, pump_name)
        settings_data = settings_list[0]

        self.assert_equals(settings_data['type'], 'pumpSettings')
