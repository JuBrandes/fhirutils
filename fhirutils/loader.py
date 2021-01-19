import requests
import json
import random
import string
import time
# import csv


class Loader():
    """A class that provides methods to download FHIR-resources into a bundle.
    This class can be used to download a patient's record as a bundle.
    Your specific resources' reference policies have to be specified via the
    config file before usage.
    Attributes
    --------------
    fhirbase : str
        a raw string representing the FHIR-base incl. trailing "/"
    logpath : str
        a raw string representing the logfile's name incl. path
    verbose : int
        integer, sets the verbosity level (0: low, 1: high verbosity [default])
    Methods
    --------------
    get Record(enc_no, req_resources, savepath, destinationfile, config_path, profile, form)
        entry method, returns bundle of resources connotated with encounter-no
    createBundle(res_lst, form)
        creates a bundle from given resource-list
    writeLogMsg(msg)
        writes a stringinto logfile
    getPatientNumber(self, enc_no, res_dict, form)
        returns the patient id that belongs to the encounter id
    getMedicationResources(med_id_lst, form):
        returns a list of medication resources matching the medication id list
    printRequestsMessage(req, search_url)
        checks http response code from given requests-obj, print to screen/log
    checkValidEncounter(enc_no)
        check if encounter-no is valid and existing on server
    loadConfig(config_path, profile)
        load FHIR profile from config file
    """

    def __init__(
                self,
                fhirbase=None,
                logpath=None,
                verbose=1
                ):
        self.logpath = logpath
        self.fhirbase = fhirbase
        self.errorstatus = False
        self.verbose = verbose
        if self.logpath is not None:
            with open(self.logpath, "w") as _:
                pass

    def getRecord(
                self,
                enc_no,
                req_resources,
                config_path,
                profile,
                savepath=None,
                destinationfile=None,
                count=100,
                form="json"
                ):
        """entry method, returns bundle of resources connotated with encounter-no
        Parameters
        --------------
        enc_no : int
            encounter id, used as the patient's core identifier that is of interest
        req_resources : list of strings
            contains the the resources' description that are to be downloaded
            examples: Encounter, Patient, MedicationStatement, Medication
        savepath : raw string
            path where the bundle shall be stored
        destinationfile : raw string
            the downloaded bundle's filename, saved in 'savepath'
        config_path : raw string
            path to config file
        profile : string
            FHIR profile that is loaded from config file
            determines the resources' references
        form : string
            sets FHIR represantation: json or xml (not implemented yet)
        count : integer
            matches FHIR-search's _count=, default 100
        Return
        --------------
        bundle as a json object
        """

        enc_no = [enc_no]
        res_dict = self.loadConfig(config_path, profile)

        format_dict = {
                "json": "&_format=json&_count=" + str(count),
                "xml": "&_format=xml&_count=" + str(count)
            }

        if not self.checkValidEncounter(enc_no):
            print(
                "Encounter identifier validation failed, \
                check server connection and encounter identifier. Aborting...")
            exit()

        pat_no = self.getPatientNumber(enc_no, res_dict, form)

        for v in res_dict.values():
            if v[1][0] == "encounter_id":
                v[1][0] = enc_no[0]
            elif v[1][0] == "patient_id":
                v[1][0] = pat_no[0]

        res_lst = []
        med_id_lst = []

        for resource in req_resources:
            if resource == "Medication":
                med_res = self.getMedicationResources(med_id_lst)
                res_lst.extend(med_res)
            else:
                search_url = self.fhirbase + \
                            resource + \
                            res_dict[resource][0] + \
                            str(res_dict[resource][1][0]) + \
                            format_dict[form]
                if self.verbose > 0:
                    print(search_url)
                req = requests.get(search_url)
                self.printRequestsMessage(req, search_url)
                downloads = str(req.content, encoding='cp1252')

                if form == "json":
                    json_data = json.loads(downloads)
                    try:
                        for item in json_data["entry"]:
                            res_lst.append(item)
                            if (
                                resource == "MedicationAdministration" or
                                resource == "MedicationStatement" or
                                resource == "MedicationRequest"
                            ):
                                try:
                                    med_id = item["resource"]["medicationReference"]["reference"]
                                    med_id = med_id.split("Medication/", 1)[1]
                                    if med_id not in med_id_lst:
                                        med_id_lst.append(med_id)
                                except KeyError:
                                    pass
                    except KeyError:
                        msg = "Encounter ID " + \
                            enc_no[0] + \
                            " -> Requested resource (" + \
                            resource + \
                            "): No resource found"
                        self.errorstatus = True
                        if self.logpath is not None:
                            self.writeLogmsg(msg)

        bundle = self.createBundle(res_lst, form)

        if savepath is not None:
            path_str = savepath + "/" + destinationfile
            with open(path_str, "w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, indent=4)
                print("-----------------------------------------------")
                print("Bundle created and saved to " + path_str + ".")
                if self.errorstatus:
                    print("Errors have occured. Please check the log, if enabled.")

        return bundle

    def createBundle(self, res_lst, form):
        bundle = None
        identifier = "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(40)
        )
        timestring = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        timestring = "{0}:{1}".format(
                        timestring[:-2],
                        timestring[-2:]
                    )

        if form == "json":
            bundle = {
                "resourceType": "Bundle",
                "type": "transaction",
                "entry": res_lst,
                "id": identifier,
                "meta": {"lastUpdated": timestring},
            }

        return bundle

    def writeLogmsg(self, msg):
        with open(self.logpath, "a") as f:
            f.writelines(msg + "\n")

    def getPatientNumber(self, enc_no, res_dict, form="json"):
        pat_no = None
        search_url = self.fhirbase + "Patient" + res_dict["Patient"][0] + enc_no[0]
        print(search_url)
        req = requests.get(search_url)
        downloads = str(req.content, encoding='cp1252')
        if form == "json":
            json_data = json.loads(downloads)
            try:
                for item in json_data["entry"]:
                    pat_no = item["resource"]["id"]
                return [pat_no]
            except KeyError:
                msg = "Encounter ID " + \
                    enc_no[0] + \
                    " -> Requested resource (Patient): No resource found"
                print(msg)
                self.errorstatus = True
                self.writeLogmsg(msg)

    def getMedicationResources(self, med_id_lst, form="json"):
        res_lst = []
        for med in med_id_lst:
            search_url = self.fhirbase + "Medication?_id=" + med
            if self.verbose > 0:
                print(search_url)
            req = requests.get(search_url)
            self.printRequestsMessage(req, search_url)
            downloads = str(req.content, encoding='cp1252')
            if form == "json":
                json_data = json.loads(downloads)
                try:
                    for item in json_data["entry"]:
                        res_lst.append(item)
                except KeyError:
                    msg = "Medication ID " + \
                        med + \
                        " -> Requested resource (Medication): No resource found"
                    self.errorstatus = True
                    if self.logpath is not None:
                        self.writeLogmsg(msg)

        return [res_lst]

    def printRequestsMessage(self, req, search_url):
        if req.ok:
            if self.verbose > 0:
                print("Download completed.")
            return True
        else:
            errormsg = "Download Error: " + search_url
            self.errorstatus = True
            if self.verbose > 0:
                print(errormsg)
            self.writeLogmsg(errormsg)
            return False

    def checkValidEncounter(self, enc_no):
        search_url = self.fhirbase + "Encounter?_id=" + enc_no[0]
        req = requests.get(search_url)
        errormsg = "Encounter identifier validation failed."
        if not self.printRequestsMessage(req, search_url):
            self.writeLogmsg(errormsg)
            return False
        self.printRequestsMessage(req, search_url)
        downloads = str(req.content, encoding='cp1252')
        json_data = json.loads(downloads)
        if json_data["total"] > 0:
            return True
        else:
            self.writeLogmsg(errormsg)
            return False

    def loadConfig(self, config_path, profile):
        res_dct = {}
        with open(config_path, "r") as f:
            json_data = json.load(f)

        for _ in json_data[profile]:
            res_dct[_["resourceType"]] = [_["loadingSuffix"], [_["loadingCode"]]]

        return res_dct


if __name__ == "__main__":
    logpath = r"log.txt"
    fhirbase = r"https://mii-agiop-3p.life.uni-leipzig.de/fhir/"
    req_resources = ["Encounter", "Patient", "MedicationStatement", "Medication"]
    savepath = r""  # set path
    config_path = r"config.json"
    profile = "KDS"
    count = 10000

    loader = Loader(fhirbase=fhirbase, logpath=logpath)
    encounters = ["1", "439", "UKB003E-1"]

    for enc in encounters:
        destinationfile = enc + ".json"
        enc_no = enc
        loader.getRecord(
            enc_no,
            req_resources,
            config_path,
            profile,
            savepath,
            destinationfile,
            count
            )
