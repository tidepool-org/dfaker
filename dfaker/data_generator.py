from datetime import datetime

from . import tools
from . import bg_simulator
from .bolus import bolus, generate_boluses
from .wizard import wizard
from .pump_settings import make_pump_settings
from .cbg import cbg, apply_loess
from .smbg import smbg
from .basal import scheduled_basal


def dfaker(num_days, zonename, date_time, gaps, smbg_freq, pump_name):
    """ Generate data for a set num_days within a single timezone
    """
    dfaker = []
    solution = bg_simulator.simulate(num_days)

    start_time = datetime(date_time.year, date_time.month, date_time.day,
                          date_time.hour, date_time.minute)
    zone_offset = tools.get_offset(zonename, start_time)

    cbg_gluc, cbg_time, smbg_gluc, smbg_time = apply_loess(solution,
                                                           num_days=num_days,
                                                           gaps=gaps)
    cbg_timesteps = tools.make_timesteps(start_time, zone_offset, cbg_time)
    smbg_timesteps = tools.make_timesteps(start_time, zone_offset, smbg_time)

    b_carbs, b_carb_timesteps, w_carbs, w_carb_timesteps, w_gluc = (
            generate_boluses(solution, start_time, zonename=zonename,
                             zone_offset=zone_offset))

    settings_data = make_pump_settings(start_time, zonename=zonename,
                                       pump_name=pump_name)
    basal_data, pump_suspended = scheduled_basal(start_time,
                                                 num_days=num_days,
                                                 zonename=zonename,
                                                 pump_name=pump_name)
    bolus_data = bolus(start_time, b_carbs, b_carb_timesteps,
                       no_bolus=pump_suspended, zonename=zonename,
                       pump_name=pump_name)
    wizard_data, iob_data = (wizard(start_time, w_gluc, w_carbs,
                                    w_carb_timesteps, bolus_data=bolus_data,
                                    no_wizard=pump_suspended,
                                    zonename=zonename, pump_name=pump_name))
    cbg_data = cbg(cbg_gluc, cbg_timesteps, zonename=zonename)
    smbg_data = smbg(smbg_gluc, smbg_timesteps, stick_freq=smbg_freq,
                     zonename=zonename)

    dfaker = (dfaker + settings_data + basal_data + bolus_data + wizard_data +
              cbg_data + smbg_data)
    return dfaker
