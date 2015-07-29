#Dfaker Developer Documentation

--------------
##Purpose

Dfaker is a fake diabetes data generator designed to fit Tidepool's data model description. Running dfaker will generate a JSON-formatted file with a desired number of days of fake diabetes data. For a reference to the data model and the format specifications, [click here](http://developer.tidepool.io/data-model/v1/). 

##Requirements and setup

dfaker was developed using Python3. For required packages and installation, refer to the readme file.  

--------------
##Repository Organization

- `dfaker/` contains the main data generation file as well as modules for each unique datatype. Important files include:
    + `data_generator.py` defines the core dfaker function that calls each datatypes and aggregates fake data for a set number of days within a single timezone.
    + `tools.py` contains important tools used throughout dfaker to generate data.
    + `bg_simulator.py` generates the blood glucose simulator function used to create cbg data upon which every other datatype is dependent. 
    + `insulin_on_board.py` provides functions that are used to calculate and store insulin on board values for any given time during simulation.
    + `travel.py` contains functions that simulate traveling events between different timezones within the indicated `num_days` period.  
- `tests/` contains the test suites for the different datatypes dfaker generates. 
- `dfaker_cli.py` contains the command line tools to generate data according to desired specifications. 
- `device-data.json` is the resulting json file generated after running dfaker.

--------------
##Using the command line tools

The command line tools were built using python's argparse. They allow the user to override the default dfaker settings and customize the output data file. Default settings are stored in a params dictionary and look like this: 
```python
params = {
        'datetime' : datetime.strptime('2015-01-01 00:00', '%Y-%m-%d %H:%M'), #default datetime settings
        'zone' : 'US/Pacific', #default zone
        'num_days' : 180, #default number of days to generate data for
        'file' : 'device-data.json', #default json file name 
        'minify' : False, #compact storage option false by default 
        'gaps' : False, #randomized gaps in data, off by default 
        'smbg_freq' : 6, #default number of fingersticks per day
        'travel': False, #no traveling takes place by default 
        'pump_name': 'Medtronic' #default pump name
    }  
```
To override any of the default settings, the user can specify desired options using the command line tools in terminal. The `parse()` function in `dfaker_cli.py` parses the user input and terminates dfaker with an error message if bad input was given. If inputs are valid, `parse()` replaces the appropriate default values in `params` with  user specified settings. Command line tools include the following options:

- `-z` allows the user to specify a timezone in which the data simulation will take place.
    + Timezone must be found in `pytz.common_timezones`.
- `-d` allows the user to specify a start date for the simulation.
    + Date must have a YYYY-MM-DD format. 
- `-t` allows the user to specify a start time.
    + Time must have a HH:MM format.
- `-n` Allows the user to set the number of days over the course of which dfaker will run.
    + `num_days` input must be an integer. 
- `-f` lets the user set a desired name for the output json file.
    + file must have a .json extension. 
- `-m` selecting this option creates a compact json file with no tabs or spacing.
- `-g` selecting this options creates randomized gaps in the data.
- `-s` allows the user to set a desired fingerstick frequency. 
    + The only options for this command are `high` (average of 8 fingetersticks a day), `average` (6 a day) or `low` (3 a day).
- `-r` sets the travel parameter to True, generating data within multiple timezones.
- `-p` allows the user to specify the pump used for data generation.
    + Currently, only `Medtronic`, `Tandem` and `OmniPod` pumps are supported. 

Running the help command
```
python3 dfaker_cli.py -h
```
will result in this help message:
```
usage: dfaker_cli.py [-h] [-z ZONE] [-d DATE] [-t TIME] [-n NUM_DAYS]
                     [-f FILE] [-m] [-g] [-s SMBG_FREQ] [-r] [-p PUMP]

optional arguments:
 -h,           --help               show this help message and exit
 -z ZONE,      --timezone ZONE      Local timezone
 -d DATE,      --date DATE          Date in the following format: YYYY-MM-DD
 -t TIME,      --time TIME          Time in the following format: HH:MM
 -n NUM_DAYS,  --num_days NUM_DAYS  Number of days to generate data
 -f FILE,      --output_file FILE   Name of output json file
 -m,           --minify             Minify the json file
 -g,           --gaps               Add gaps to fake data
 -s SMBG_FREQ, --smbg SMBG_FREQ     Freqency of fingersticks a day: high, average or low
 -r,           --travel             Add travel option
 -p PUMP,      --pump PUMP          Specify pump name
```

--------------
##Data generation overview

The calls for the data generation occur in the `dfaker()` function in `data_generator.py`. The output json file is formated as a list called `dfaker` that contains a dictionary entry for each event. A call to each datatype module generates dictionary entries of that type which are added in order to the `dfaker` list. 

###Getting an equation for a set `num_days`

- The first step in `dfaker()` is to obtain time-value pairs that represent cbg data. 
    + The `simulate()` function in `bg_simulator.py` takes `num_days`, and calls the `simulator()` function over and over again over the course of the specified days, essentially stitching the returned numpy lists to create the entire dataset.
    + The `simulator()` function is the most critical function of the dfaker project. It takes `initial_carbs`, `initial_sugar`, `digestion_rate`, `insulin_rate`, `total_minutes` and `start_time` as initial values, and, using a differential equation from a study on [blood glucose levels over time](http://scholarcommons.usf.edu/cgi/viewcontent.cgi?article=4830&context=ujmm), solves for the blood glucose value (in mg/dL) for each 5 minute time-period over the course of `total_minutes`. The returned value is a numpy list containing inner lists. Each inner list has the following format: 
 
        | [carb Value      | Glucose Value  | Time Representation ]|
        |------------------|----------------|----------------------|
        | [ 4.17760096e+01 | 1.16500409e+02 | 0                   ]|
        | [ 2.89573162e+01 | 1.28418084e+02 | 5                   ]|
        | [ 2.00719534e+01 | 1.36048205e+02 | 10                  ]|
        | [ (...)          | (...)          | (...)               ]|

        - The **carb values** represent a randomized carb intake (in grams).
        - The **glucose values** are derived from the differential equation (in mg/dL).
        - The **time representation** stands for the amount of elapsed minutes since the beginning of the simulation.
        - (...) stands to indicate the list goes on. 
- Next, the time-values lists are passed to `apply_loess()` in `cbg.py`. The glucose values are extracted from the solution to form smbg data (which will be filtered later), and cbg data.
    + Using `statsmodels.api`, a loess smoothing curve is applied to the cbg data, to make the results look more realistic. 
- Finally, the time representation floats are converted to epoch timesteps using the `make_timesteps()` function in `tools.py`.

###Generating boluses

- To create bolus events, the `generate_boluses()` function in `bolus.py` is called. It takes `solution` (generated earlier, refer to table above), `start_time`, `zonename`, and `zone_offset`, and filters to keep significant carb events (carb values > 10 grams). 
- After removing most bolus events that occur in the nighttime (because people rarely eat in the middle of the night), cleaning up clusters of boluses that are unrealistically close to each other, and randomly sorting bolus events into regular bolus events or bolus events accompanied by a wizard event, the `generate_boluses()` function returns numpy lists for carb events and timesteps for both wizard and bolus events (which will be used later to generate these datatypes).

###Adding Datatypes to dfaker

- The first datatype added to dfaker is always the `settings` type. This helps access settings more easily at other points in the code if necessary, because settings will always be the zeroth element in dfaker.
- Next is basal data. Basal data is generated according to the `basalSchedules` entry generated in the `settings` datatype.
    + A call to basal returns a list of dictionaries representing all basal events as well as a `pump_suspended` list
        - `pump_suspended` is a list of lists. Each inner list contains a start and an end timestemp during which the pump was suspended. This data is used later to remove bolus or wizard events during suspension period.
    + Three types of basal entries could take place:
        - `scheduled_basal` - regular basal according to settings schedule.
        - `temp_basal` - a temporary basal that overrides the scheduled basal for a randomized period of time.
        - `suspened_basal` - a manual suspension of the pump during which no basal event takes place.
            + A `deviceMeta` datatype with `subType = status` event is also created in `device_meta.py` to reflect the suspension of the pump.  

- The bolus datatype is added to dfaker next. Many times of boluses can be generated. The decision making as to which bolus should be generated is randomized in the `bolus()` function in `bolus.py`.
    + `normal_bolus` - bolus dosage given at the indicated `deviceTime`.
    + `sqaure_bolus` - bolus dose spread over indicated `duration`.
    + `dual_square_bolus` - partial dose called `normal` given at indicated `deviceTime` and the rest administered over `duration`.
    + `interrupted_normal_bolus` - normal bolus interrupted after being administered. 
    + `interrupted_dual_sqaure_bolus` - dual square bolus interrupted after being administered.
- Wizard data is added to dfaker after bolus. Each wizard event is accompanied by a bolus event. The wizard event represent the pump's recommendation, and the bolus event shows what actually happened (which could be different since the user can override wizard recommendations). 
    + To make a recommendation, the wizard access settings objects such as `insulinSensitivity`, `carbRatio`, and `bgTarget` that help calculate user specific needs. 
    + In addition insulin on board is calculated with the help of `insulin_on_board.py` module. 
    + With this information, the wizard provides a recommendation stored in `wizard_reading["recommended"]["net"]`.
    + The recommendation can either be accepted or overridden (this decision is generated randomly).
- Finally, cbg and smbg datatypes are added to dfaker. 
    + cbg data is generated from the `cbg_gluc` and `cbg_time` created earlier from `solution`.
        - cbg values over 400 or under 40 are considered out of range.
    + smbg data is generated by randomly selecting a sample of glucose events from the `solution`. The amount of events selected per day matches the `smbg_freq` values specified in `params`. 
          + smbg values are further randomized to be a bit different from cbg data and look more realistic. 
          + smbg values over 600 or under 20 are considered out of range.
- All datatypes share common fields that can be found in `common_fields.py`. 

--------------
##Travel Overview

- To simulate travel, multiple calls to `dfaker()` take place in `travel.py`. Each call to `dfaker()` occurs in a different timezone. 
    + `before_travel` calls `dfaker()` with the initial timezone.
    + `during_travel` calls `dfaker()` with a travel timezone generated randomly in `select_travel_destination()`. 
    + `after_travel` calls `dfaker()` with the initial timezone again.
- When `num_days` is greater than 30, multiple calls to `travel_event()` may take place. 
- Each time a change of timezone occurs, a `deviceMeta` datatype with `subType = timeChange` is also created.

--------------
##Calculating Insulin on Board

- To calculate insulin ob board in `insulin_on_board.py`, bolus data is first formated in the `format_bolus_for_iob_calc()` function.
    + Normal bolus events are appended to `time_vals` as lists containing a timestamp and a dose value.   
    + Square bolus and dual square bolus events are more complicated because the insulin is not given all at once and therefore the iob calculation is different.
        - the insulin is divided into one minute segments over the course of `duration`.
        - Each 1-minute segment is then added to `time-vals` as a list containing a timestamp and a dose of insulin per segment.
- An insulin on board dictionary is created with `create_iob_dict()` and can later be updated (when more boluses are generated) with `update_iob_dict()`. The IOB dict stores timestamps and corresponding iob values at these timestamps. 
- To calculate IOB a linear decay equation is used in `add_iob()`. This function is called over and over again until each insulin dose from `time_vals` goes down to zero.
- To find an iob value at any point in time, the `insulin_on_board()` can be used. It will approximate to within a 5 minute period of the desired timestamp and search the iob_dict. If no value is found, it will return 0.

--------------
##Future Steps

Adding datatypes as the data model is further developed in the future could be desired. Adding a new datatype is pretty simple. The following information will be helpful to adding new datatypes:
    - A new datatype should be contained within its own module.
    - Each datatype entry must be a dictionary.
    - Calling `common_fields.add_common_fields(name, datatype, timestamp, zonename)` is an easy way to populate all the common fields required for any datatype.
    - All other fields should be configured according to data model specifications. 

