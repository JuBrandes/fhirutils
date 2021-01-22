import requests
import json
import time
from utils import Utils
import csv


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
        self.utils = Utils()
        if self.logpath is not None:
            with open(self.logpath, "w") as _:
                pass

    def getRecord(self,
                  enc_no,
                  req_resources,
                  config_path,
                  profile,
                  savepath=None,
                  destinationfile=None,
                  count=100,
                  form="json"):
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
                            if self.validate_resolve(item) is not None:
                                item = self.validate_resolve(item)
                                res_lst.append(item)
                            if (
                                resource == "MedicationAdministration" or
                                resource == "MedicationStatement" or
                                resource == "MedicationRequest"
                            ):
                                try:
                                    med_id = item["resource"]["medicationReference"]["reference"]
                                    med_id = med_id.split("Medication/", 1)[1]
                                    if med_id not in med_id_lst and "?" not in med_id:
                                        med_id_lst.append(med_id)
                                except KeyError:
                                    pass
                    except KeyError:
                        msg = "Warning: Encounter ID " + \
                            enc_no[0] + \
                            " -> Requested resource (" + \
                            resource + \
                            "): No resource found"
                        self.errorstatus = True
                        if self.logpath is not None:
                            self.writeLogmsg(msg)

        bundle = self.utils.create_bundle(res_lst=res_lst, btype="transaction", form=form)

        if savepath is not None:
            path_str = savepath + "/" + destinationfile
            with open(path_str, "w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, indent=4)
                print("-----------------------------------------------")
                print("Bundle created and saved to " + path_str + ".")
                if self.errorstatus:
                    print("Errors have occured. Please check the log, if enabled.")

        return bundle

    def writeLogmsg(self, msg):
        with open(self.logpath, "a") as f:
            current_time = time.strftime("%m/%d/%Y, %H:%M:%S")
            msg = current_time + " " + msg + "\n"
            f.writelines(msg)

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
                msg = "Warning: Encounter ID " + \
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
                    msg = "Warning: Medication ID " + \
                        med + \
                        " -> Requested resource (Medication): No resource found"
                    self.errorstatus = True
                    if self.logpath is not None:
                        self.writeLogmsg(msg)

        return res_lst

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

    def validate_resolve(self, res):
        """
        checks if certain FHIR rules are violated and tries to resolve them

        Parameters:
        -------------
        res: a resource as json object

        Return:
        -------------
        a (in case corrected) resource as dict
        """

        to_check = self.utils.get(i="", s=res, t="resource", f="json")["value"][0]

        # checks for a certain non-resolvable medication reference occuring in
        # ID Berlin's MedicationStatements with non-standardised medication prescriptions.
        # If found: delete resource and return None object
        try:
            if "Medication/?" == to_check["resource"]["medicationReference"]["reference"]:
                msg = "Warning: MedicationStatement deleted due to non-resolvable reference ?."
                self.writeLogmsg(msg)
                return None
        except KeyError:
            pass

        # checks if there is a transaction verb. If not: add one
        if "request" not in to_check:
            res_type = self.utils.get(i="resource.resourceType",
                                      s=to_check,
                                      t="resource",
                                      f="json")["value"][0]
            res_id = self.utils.get(i="resource.id", s=to_check, t="resource", f="json")["value"][0]
            to_check["request"] = {
                "method": "PUT",
                "url": res_type + "/" + res_id
            }

        return to_check


class Connector():
    def __init__(self,
                 fhirbase_source=None,
                 fhirbase_destination=None,
                 enc_no_lst=None,
                 incr=False,
                 logpath=None,
                 verbose=1):
        self.logpath = logpath
        self.fhirbase_source = fhirbase_source
        self.fhirbase_destination = fhirbase_destination
        self.errorstatus = False
        self.verbose = verbose
        self.utils = Utils()

        if incr:
            print("Matching encounter IDs for incremental upload ...")
            fhir_search = self.fhirbase_destination + "Encounter?_summary=true"
            destination_encounters = self.get_encounters_list(fhir_search=fhir_search)
            self.enc_no_lst = []
            for item in enc_no_lst:
                if item not in destination_encounters:
                    self.enc_no_lst.append(item)
            dif = len(enc_no_lst) - len(self.enc_no_lst)
            print("Done. Skip " + str(dif) + " encounters.")
        else:
            self.enc_no_lst = enc_no_lst

        self.loader = Loader(fhirbase=self.fhirbase_source, logpath=self.logpath)

        if self.logpath is not None:
            with open(self.logpath, "w") as _:
                pass

    def connect(self,
                req_resources,
                config_path,
                profile,
                method="PUT",
                count=100,
                form="json"):

        for enc in self.enc_no_lst:
            self.upload_record(enc,
                               req_resources,
                               config_path,
                               profile,
                               method=method,
                               count=count,
                               form=form)

    def upload_record(self,
                      enc_no,
                      req_resources,
                      config_path,
                      profile,
                      method="PUT",
                      count=100,
                      form="json"):

        bundle = self.loader.getRecord(enc_no,
                                       req_resources,
                                       config_path,
                                       profile,
                                       count=count,
                                       form=form)

        with open("testbundle.json", "w") as f:
            json.dump(bundle, f)

        req = None
        if method == "PUT":
            req = requests.put(self.fhirbase_destination, json=bundle)
            print(req.reqtext)
        elif method == "POST":
            req = requests.post(self.fhirbase_destination, json=bundle)

        if req.ok:
            print("Upload completed...")
        elif req.ok is False:
            msg = "Upload Error. Status code: " + str(req.status_code)
            print(msg)
            self.writeLogmsg(msg)
            content = json.loads(req.content)
            errormsg = self.utils.get(i="issue.0.details.text",
                                      s=content,
                                      t="resource",
                                      f="json")["value"]
            self.writeLogmsg(errormsg)

    def writeLogmsg(self, msg):
        with open(self.logpath, "a") as f:
            current_time = time.strftime("%m/%d/%Y, %H:%M:%S")
            msg = current_time + " " + msg + "\n"
            f.writelines(msg)

    def get_encounters_list(self, fhir_search=None):
        resources = self.utils.link_search(fhir_search=fhir_search)
        encounters = self.utils.get(i="X.id", s=resources, t="resource", f="json")

        return encounters["value"].values


if __name__ == "__main__":
    logpath = r"log_test.txt"
    fhirbase_source = r""  # set fhirbase of source server
    fhirbase_destination = r""  # set fhirbase of destination server
    req_resources = ["Encounter", "Patient", "MedicationStatement", "Medication"]
    config_path = r"config.json"
    profile = "ID Logik"
    count = 10000
    method = "POST"

    encounters = []
    with open("encounters.csv", "r") as f:  # a csv-file with encounter IDs. 1 encounter ID = 1 line
        csv_reader = csv.reader(f)
        _enc = [x[0] for x in csv_reader]
        for e in _enc:
            if e not in encounters:
                encounters.append(e)

    connector = Connector(fhirbase_source=fhirbase_source,
                          fhirbase_destination=fhirbase_destination,
                          enc_no_lst=encounters,
                          incr=True,
                          logpath=logpath)

    connector.connect(req_resources,
                      config_path,
                      profile,
                      method=method,
                      count=count)
