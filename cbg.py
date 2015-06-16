import random
import statsmodels.api as sm
import make_gaps
import common_fields
import tools

def apply_loess(solution, num_days, gaps):
    """Solves the blood glucose equation over specified period of days 
        and applies a loess smoothing regression to the data 
        Returns numpy arrays for glucose and time values 
    """
    #solving for smbg valuesn
    smbg_gluc = solution[:, 1]
    smbg_time = solution[:, 2]

    #make gaps in cbg data, if needed
    solution = make_gaps.gaps(solution, num_days=num_days, gaps=gaps)
    #solving for cbg values 
    cbg_gluc = solution[:, 1]
    cbg_time = solution[:, 2]
    #smoothing blood glucose eqn
    lowess = sm.nonparametric.lowess
    smoothing_distance = 1.4 #1.4 minutes
    fraction = (smoothing_distance / (num_days * 60 * 24)) * 100
    result = lowess(cbg_gluc, cbg_time, frac=fraction, is_sorted=True)
    smoothed_cbg_time = result[:, 0]
    smoothed_cbg_gluc = result[:, 1]
    return smoothed_cbg_gluc, smoothed_cbg_time, smbg_gluc, smbg_time

def cbg(gluc, timesteps, zonename):
    cbg_data = []
    for value, timestamp in zip(gluc, timesteps):
        cbg_reading = {}
        cbg_reading = common_fields.add_common_fields('cbg', cbg_reading, timestamp, zonename)
        cbg_reading["value"] = tools.convert_to_mmol(value)
        cbg_reading["units"] = "mmol/L"
        if value >= 400:
            cbg_reading["annotation"] = [{"code": "bg/out-of-range", "threshold": 400, "value": "high"}]
            cbg_reading["value"] = tools.convert_to_mmol(401)
        elif value <= 40:
            cbg_reading["annotation"] = [{"code": "bg/out-of-range", "threshold": 40, "value": "low"}]
            cbg_reading["value"] = tools.convert_to_mmol(39)
        cbg_data.append(cbg_reading)
    return cbg_data