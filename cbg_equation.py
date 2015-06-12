import numpy as np 
import matplotlib.pyplot as plt 
from scipy.integrate import odeint 
import random
from scipy import interpolate
import statsmodels.api as sm

def simulator(initial_carbs=121.7, initial_sugar=90, digestion_rate=0.0453, insulin_rate=0.0224, minutes=100, start_time=0):
    """Constructs a blood glucose equation using the following initial paremeters:
        initial_carbs -- the intake amount of carbs 
        initial_sugar -- the baseline value of glucose at time zero
        digestion_rate -- how quickly food is digested
        insulin_rate -- how quickly insulin is released.
    """
    def model_func(y, t):
        Ci = y[0]
        Gi = y[1]
        f0 = -digestion_rate * Ci
        f1 = digestion_rate * Ci - insulin_rate * (Gi - initial_sugar)
        return [f0, f1]

    y0 = [initial_carbs, initial_sugar]
    t = np.linspace(start_time, start_time + minutes, minutes / 5) #timestep every 5 minutes 
    carb_gluc = odeint(model_func, y0, t)
    cgt = zip(carb_gluc, t)
    carb_gluc_time = []
    for elem in cgt:
        carb = elem[0][0]
        gluc = elem[0][1]
        time = elem[1]
        carb_gluc_time.append([carb, gluc, time])
    np_cgt = np.array(carb_gluc_time)
    return np_cgt

def assign_carbs(sugar, last_carbs, sugar_in_range):
    """ Assign next 'meal' event based on:
        sugar -- the current glucose level 
        last_carb -- the previous carb value
        sugar_in_range -- list of previous consecutive 'in range' sugar events 
    """
    if sugar >= 240:
        carbs = random.uniform(-300, -290)
    elif sugar >= 200:
        carbs = random.triangular(-250, -180, -220)
    elif len(sugar_in_range) >= 3:
        high_or_low = random.randint(0,1) #if sugar in range, randomley generate high or low event
        if high_or_low == 0:
            carbs = random.uniform(230, 250)
        else:
            carbs = random.uniform(-250, 250)
    elif sugar <= 50:
        carbs = random.triangular(270, 300, 290)
    elif sugar <= 80:
        carbs = random.triangular(200, 250, 230)
    elif last_carbs > 50:
        carbs = random.uniform(-190, -170)
    else:
        carbs = random.triangular(-50, 100, 60)
    return carbs

def stitch_func(num_days=180):
    days_in_minutes = num_days * 24 * 60
    sugar = random.uniform(80, 180) #start with random sugar level
    last_carbs = random.uniform(-60, 300)
    next_time = 0
    sugar_in_range = []
    simulator_data = []
    while next_time < days_in_minutes:
        if int(sugar) in range(80, 195):
            sugar_in_range.append(sugar)
        else:
            sugar_in_range = []         
        carbs = assign_carbs(sugar, last_carbs, sugar_in_range)
        digestion = random.uniform(0.04, 0.08)
        insulin_rate = random.uniform(0.002, 0.05)
        minutes = random.uniform(100, 200) #change this to higher numbers for less frequent events
        result = simulator(carbs, sugar, digestion, insulin_rate, minutes, next_time)
        simulator_data.append(result)       
        sugar = result[-1][1]
        next_time += minutes + 5 #add 5 minutes to avoid duplicates 
        last_carbs = carbs
    stitched = []
    for array in simulator_data:
        for cgt_val in array:
            stitched.append(cgt_val)
    np_stitched = np.array(stitched)
    return np_stitched