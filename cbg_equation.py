import numpy as np 
import matplotlib.pyplot as plt 
from scipy.integrate import odeint 
import random
from scipy import interpolate

plt.ion()

def simulator(initial_carbs=121.7, initial_sugar=90, digestion_rate=0.0453, insulin_rate=0.0224, minutes=100, start_time=0):
	"""Constructs a blood glucose equation using the foloowing initial paremeters:
		initial_carbs, the intake amount of carbs -- a bolus or a meal
		initial_sugar, the baseline value of glucose at time zero
		digestion_rate, how quickly food is digested
		insulin_rate, how quickly insulin is released.
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
	numpy_cgt = np.array(carb_gluc_time)
	return numpy_cgt

def stich_func(num_days=1):
	days_in_minutes = num_days * 24 * 60
	sugar = random.uniform(60, 300) #start with random sugar level
	start_time = 0
	simulator_data = []
	while start_time < days_in_minutes:
		carbs = random.uniform(-60, 70)
		digestion = random.uniform(0.004, 0.08)
		insulin_rate = random.uniform(0.002, 0.05)
		minutes = random.uniform(100, 200) #time in minutes
		result = simulator(carbs, sugar, digestion, insulin_rate, minutes, start_time)
		simulator_data.append(result)		
		sugar = result[-1][1]
		start_time += minutes
	stiched = []
	for array in simulator_data:
		for cgt_val in array:
			stiched.append(cgt_val)
	np_stiched = np.array(stiched)
	return np_stiched

solution = stich_func()
carbs = solution[:, 0]
glucose = solution[:, 1]
t = solution[:, 2]

plt.figure()
plt.plot(t, carbs, label='Carbs')
plt.plot(t, glucose, label='Glucose')
plt.xlabel('Time (Minutes)')
plt.ylabel('Blood Glucose level (mg/dL)')
plt.legend(['carbs', 'glucose'])
plt.title("Glucose vs. Time")
plt.savefig('stich3.png')
