import requests
import json
import random
import string
import time

class FhirUtils():
    def __init__(self, fhirbase=None, logpath=None):
        self.logpath = logpath
        self.fhirbase = fhirbase
        if self.logpath is not None:
            with open(self.logpath, "w") as f:
                pass
        

    def getRecord(self, enc_no, req_resources, savepath, form="json"):
        enc_no = [enc_no]
        if not self.checkValidEncounter(enc_no):
            print("Encounter identifier validation failed, check server connection and encounter identifier. Aborting...")
            exit()

        med_id_lst = []
        
        pat_no = self.getPatientNumber(enc_no, form)
        res_dict = { 
                "MedicationRequest" : ["?encounter=", None],
                "MedicationStatement" : ["?subject=", pat_no],
                "Encounter" : ["?_id=", enc_no],
                "Patient" : ["?_has:Encounter:patient:_id=", enc_no],
                "MedicationAdministration" : ["?subject=", pat_no],
                "Observation": ["?subject=", pat_no],
            }

        format_dict = {
                "json" : "&_format=json",
                "xml" : "&_format=xml"
        }


        res_lst = []
        

        for resource in req_resources:
            if resource == "Medication":
                med_res = self.getMedicationResources(med_id_lst)
                res_lst.extend(med_res)
            else:
                search_url = self.fhirbase + resource + res_dict[resource][0] + str(res_dict[resource][1][0]) + format_dict[form]
                print(search_url)
                req = requests.get(search_url)
                self.printRequestsMessage(req, search_url)
                downloads = str(req.content, encoding='cp1252')
                
                with open(savepath + "/" + resource + ".json", "w")  as f:
                    f.write(downloads)

                if form == "json":
                    json_data = json.loads(downloads)
                    try:
                        for item in json_data["entry"]:
                            res_lst.append(item)
                            if resource == "MedicationAdministration" or resource == "MedicationStatement" or resource == "MedicationRequest":
                                try:
                                    med_id = item["resource"]["medicationReference"]["reference"]
                                    med_id = med_id.split("Medication/",1)[1]
                                    if med_id not in med_id_lst:
                                        med_id_lst.append(med_id)
                                except KeyError:
                                    pass
                    except KeyError:
                        msg = "Encounter ID " + enc_no[0] + " -> Requested resource (" + resource + "): No resource found"
                        if self.logpath is not None:
                            self.writeLogmsg(msg)            

        bundle = self.createBundle(res_lst, form)

        with open("tests/test.json", "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=4)

    def createBundle(self, res_lst, form):
        identifier = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(40))
        timestring = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
        timestring = "{0}:{1}".format(
                        timestring[:-2],
                        timestring[-2:]
                    )

        if form == "json":
            bundle = {  "resourceType" : "Bundle",
                        "type" : "searchset",
                        "entry" : res_lst,
                        "total" : len(res_lst),
                        "id" : identifier,
                        "meta" : { "lastUpdated" : timestring},
                   }

        return bundle

    def writeLogmsg(self, msg):
        with open(self.logpath, "a") as f:
            f.writelines(msg + "\n")

    def getPatientNumber(self, enc_no, form="json"):
        search_url = self.fhirbase + "Patient?_has:Encounter:patient:_id=" + enc_no[0]
        print(search_url)
        print(enc_no)
        req = requests.get(search_url)
        downloads = str(req.content, encoding='cp1252')
        if form == "json":
            json_data = json.loads(downloads)
            try:
                for item in json_data["entry"]:
                    pat_no = item["resource"]["id"]
                return [pat_no]
            except KeyError:
                msg = "Encounter ID " + enc_no[0] + " -> Requested resource (Patient): No resource found"
                print(msg)
                self.writeLogmsg(msg)


    def getMedicationResources(self, med_id_lst, form="json"):
        res_lst = []
        for med in med_id_lst:
            search_url = self.fhirbase + "Medication?_id=" + med
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
                    msg = "Medication ID " + med + " -> Requested resource (Medication): No resource found"
                    if self.logpath is not None:
                        self.writeLogmsg(msg)


        return [res_lst]

    def printRequestsMessage(self, req, search_url, verbose=1):
        if req.ok:
            if verbose > 0:
                print("Download completed.")
            return True
        else:
            errormsg = "Download Error: " + search_url
            if verbose > 0:
                print(errormsg)
            self.writeLogmsg(errormsg)
            return False

    def checkValidEncounter(self, enc_no):
        search_url = self.fhirbase + "Encounter?_id=" + enc_no[0]
        req = requests.get(search_url)
        errormsg = "Encounter identifier validation failed."
        if not self.printRequestsMessage(req, search_url, verbose=0):
            self.writeLogmsg(errrormsg)
            return False
        self.printRequestsMessage(req, search_url)
        downloads = str(req.content, encoding='cp1252')
        json_data = json.loads(downloads)
        if json_data["total"] > 0:
            return True
        else:
            self.writeLogmsg(errormsg)
            return False



        









if __name__ == "__main__":
    logpath = r"log.txt"
    #fhirbase = r"https://mii-agiop-3p.life.uni-leipzig.de/fhir/"
    fhirbase = r"http://127.0.0.1:8080/"
    req_resources = [ "Encounter", "Patient", "Observation", "MedicationAdministration", "MedicationStatement", "Medication"]
    savepath = r"tests"
    enc_no = "1"
    utils = FhirUtils(fhirbase=fhirbase, logpath=logpath)
    utils.getRecord(enc_no, req_resources, savepath)