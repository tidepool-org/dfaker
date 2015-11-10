import numpy as np
from scipy.integrate import odeint
import random


def simulator(initial_carbs, initial_sugar, digestion_rate, insulin_rate,
              total_minutes, start_time):
    """Constructs a blood glucose equation using the following initial
       paremeters:

       initial_carbs -- the intake amount of carbs
       initial_sugar -- the baseline value of glucose at time zero
       digestion_rate -- how quickly food is digested
       insulin_rate -- how quickly insulin is released
       total_minutes -- amount of time (in minutes) this simulation will
                        last_carbs
       start_time -- start time (in minutes), point on timeline where this
                     simulation will begin
    """
    def model_func(y, t):
        Ci = y[0]
        Gi = y[1]
        f0 = -digestion_rate * Ci
        f1 = digestion_rate * Ci - insulin_rate * (Gi - initial_sugar)
        return [f0, f1]

    y0 = [initial_carbs, initial_sugar]
    # timestep every 5 minutes
    t = np.linspace(start_time, start_time + total_minutes, total_minutes / 5)
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
        # if sugar in range, randomley generate high or low event
        high_or_low = random.randint(0, 1)
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


def simulate(num_days):
    days_in_minutes = num_days * 24 * 60
    sugar = random.uniform(80, 180)  # start with random sugar level
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
        # total minutes for a single simulation
        total_minutes = random.randint(100, 200)
        # make sure total minutes does not exceed max num_days
        if total_minutes + next_time > days_in_minutes:
            total_minutes = days_in_minutes - next_time
        result = simulator(carbs, sugar, digestion, insulin_rate,
                           total_minutes, next_time)
        simulator_data.append(result)
        sugar = result[-1][1]
        # add 5 extra minutes to avoid duplicates
        next_time += total_minutes + 5
        last_carbs = carbs
    stitched = []
    for array in simulator_data:
        for cgt_val in array:
            stitched.append(cgt_val)
    np_stitched = np.array(stitched)
    return np_stitched
