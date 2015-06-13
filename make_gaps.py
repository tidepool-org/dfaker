import random
import numpy as np

def gaps(data, params):
    """ Create randomized gaps in fake data if user selects the gaps option
        Returns data with gaps if gaps are selected, otherwise returns full data set 
    """
    if params["gaps"]:
        solution_list = solution.tolist()
        gap_list = create_gap_list(params, solution)
        for gap in gap_list:
            solution_list = remove_gaps(solution_list, gap[0], gap[1])
        new_solution = np.array(solution_list)
        return new_solution
    return data

def create_gap_list(params, time_gluc):
    """ Returns sorted list of lists that represent indecies to be removed.
        Each inner list is a two element list containing a start index and an end index
    """
    gaps = random.randint(1 * params['num_days'], 3 * params['num_days']) # amount of gaps  
    gap_list = []
    for _ in range(gaps):
        gap_length = random.randint(10, 40) # length of gaps in 5-min segments
        start_index = random.randint(0, len(time_gluc)) 
        if start_index + gap_length > len(time_gluc):
            end_index = len(time_gluc) - 5
        else:
            end_index = start_index + gap_length
        gap_list.append([start_index, end_index])
    gap_list.sort()
    gap_list.reverse()
    return gap_list 

def remove_gaps(data, start, end):
    return data[:start] + data[end:]