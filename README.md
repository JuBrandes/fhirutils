# fhirutils
A package that provides functionality for FHIR (Fast Healthcare Interoperability Resources)

## Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. Caution: This project is still under development and not yet deployed for a live system. Usage in a real life situation is not recommended!

### Prerequisites
Following prerequisites have to be met:
- Python version 3 or newer
- Pandas version 1.05 or newer 
```
pip install pandas
```

### Installing
Navigate to your preferred destination folder and clone the repository:
```
git clone https://github.com/JuBrandes/fhirutils/
```

## Features
The features will constantly grow during development. New features will be described here.
For using the features you can either import the project into your namespace or you can use the py-files directly. The latter method is described below.

### Connect two FHIR servers to transfer bundles
The Connector class can be used to download a patient's record according to his/her encounter id from FHIR server A. This record then is automatically uploaded to FHIR server B. To test the class do this:
- open fhirutils/loader.py
- add resp. change the FHIR servers' urls (fhirbase_source, fhirbase_destination)
- if you changed the source url make shure you added a valid encounter id that exists on FHIR server A
- Maybe you have to add a profile in config.json to meet the resources' references between each other, but at first you can give it a try with the predefined "KDS" profile.
- run the script

### Download a patient's record to a FHIR bundle
The Loader class in fhirutils/loader.py provides a functionality of downloading a patient's record if the encounter id is known. This is the first step of Connector.
Open fhirutils/loader.py and scroll to the file's end. Here you can set the required parameters and call Loader. 


### Get an item from a FHIR resource by a json pathway
The Utils class in fhirutils/utils.py provides a method get() that accesses one or more values in a FHIR resource by giving the path that identifies the value of interest.
A path example for a FHIR bundle:
```
entry.X.resource.id
```
X means: This element is a list, browse every entry in this list. If you are interested in only one entry you can type e.g. for the first entry:
```
entry.0.resource.id
```
The depth of the given path is variable. For example you can get every resource from a bundle with this path:
```
entry.X.resource
```
As above: open fhirutils/utils.py and scroll to the file's end. All parameters are set for a test run.
