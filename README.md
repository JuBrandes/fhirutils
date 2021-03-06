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
The Connector class can be used to download a patient's record according to his/her encounter id from FHIR server A. This record then is automatically uploaded to FHIR server B. The bundle will contain every desired resource type that is referenced by the given encounter ID. To test the class do this:
- open fhirutils/loader.py
- add resp. change the FHIR servers' urls (fhirbase_source, fhirbase_destination)
- if you changed the source url make shure you added a valid encounter id that exists on FHIR server A
- Maybe you have to add a profile in config.json to meet the resources' references between each other, but at first you can give it a try with the predefined "KDS" ("Kerndatensatz") profile.
- run the script

#### Parameters/Attributes
##### Connector()
- fhirbase_source: the source's FHIR-base, e.g.: "https://vonk.fire.ly/"
- fhirbase_destination: the destination's FHIR-base
- enc_no_lst: a list containing encounter IDs that are to be transferred
- incr: if "True" -> encounters that are given with enc_no_lst but are already existing on destination server are omitted
- logpath: a path + filename where the logfile is to be saved, e.g.: "/home/xyz/log.txt"

##### Connector.connect()
- req_resources: a list with the resources that are to be transferred, e.g.: ["Encounter, "Patient", "MedicationStatement", "Medication"]. Please note that "Medication" MUST be the last item, if it is to be included.
- config_path: path to config.json
- profile: the profile key in config.json that represents the references among the resources on the source FHIR server.
- method: the http-request method that is to be used, "POST" or "PUT". If in doubt: Try "POST".
- count: number of resources in one FHIR-search result. Not stable, will be obsolete soon. Preferably you don't touch it and use the default (100).

### Download a patient's record to a FHIR bundle
The Loader class in fhirutils/loader.py provides a functionality of downloading a patient's record if the encounter id is known. Basically this is the first step of Connector.
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
