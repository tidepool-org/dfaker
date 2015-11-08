#Tidepool Dfaker 

[![Build Status](https://travis-ci.org/tidepool-org/dfaker.png)](https://travis-ci.org/tidepool-org/dfaker)

Dfaker is a command line tool that generates fake diabetes data. It is designed to fit Tidepool's data model description, creating data for any desired numbers of days. For a reference to the data model and the format specifications, [click here](http://developer.tidepool.io/data-model-v1/v1/). Running dfaker will generate a JSON-formatted file. An example data file, ran with the default settings can be found [here](https://github.com/tidepool-org/dfaker/blob/master/device-data.json). For further reference about dfaker, read the developer documantation [here](https://github.com/tidepool-org/dfaker/blob/master/developer_documentation.md).

#Set Up

Dfaker runs with python3. In addition, using the Anaconda scientific Python distribution is recommended as the easiest way of getting all project dependencies. 
The anaconda installation for python3 can be [found here](http://continuum.io/downloads#py34).

Alternatively, installing the following packages will work as well:
* pytz
* numpy
* statsmodels
* nose
* pandas
* patsy
* python-dateutil
* scipy
* six

#Credits

The implementation for the blood glucose model equation was based on a mathematics paper on [blood glucose levels](http://scholarcommons.usf.edu/cgi/viewcontent.cgi?article=4830&context=ujmm). 

Citation: 
Estela, Carlos (2011) "Blood Glucose Levels," Undergraduate Journal of Mathematical Modeling: One + Two: Vol. 3: Iss. 2, Article 12. 
DOI: http://dx.doi.org/10.5038/2326-3652.3.2.12 
Available at: http://scholarcommons.usf.edu/ujmm/vol3/iss2/12
