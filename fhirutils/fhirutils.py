import requests
import json
import random
import string
import time

class FhirUtils():
    def __init__(self, fhirbase, logpath):
        self.logpath = logpath
        self.fhirbase = fhirbase
        with open(self.logpath, "w") as f:
            pass

    def getRecord(self, enc_no, req_resources, savepath, form="json"):
        pat_no = []
        med_id_lst = []
        enc_no = list(enc_no)
        res_dict = { 
                "MedicationRequest" : ["?encounter=", None],
                "MedicationStatement" : ["?subject=", pat_no],
                "Encounter" : ["?_id=", enc_no],
                "Patient" : ["?_has:Encounter:patient:_id=", enc_no],
                "MedicationAdministration" : ["?subject=", pat_no],
                "Observation": ["?subject=", pat_no],
                "Medication": ["?_id="]
            }

        format_dict = {
                "json" : "&_format=json",
                "xml" : "&_format=xml"
        }

        res_lst = []
        

        for resource in req_resources:
            if resource == "Medication":
                for med in med_id_lst:
                    search_url = self.fhirbase + resource + res_dict[resource][0] + med
                    print(search_url)
                    req = requests.get(search_url)
                    downloads = str(req.content, encoding='cp1252')
                    if form == "json":
                        json_data = json.loads(downloads)
                        for item in json_data["entry"]:
                            res_lst.append(item)
            else:
                search_url = self.fhirbase + resource + res_dict[resource][0] + str(res_dict[resource][1][0]) + format_dict[form]
                req = requests.get(search_url)
                downloads = str(req.content, encoding='cp1252')
                print(search_url)
                with open(savepath + "/" + resource + ".json", "w")  as f:
                    f.write(downloads)
                if form == "json":
                    json_data = json.loads(downloads)
                    try:
                        for item in json_data["entry"]:
                            res_lst.append(item)
                            if resource == "Patient":
                                pat_no.append(item["resource"]["id"])
                            if resource == "MedicationAdministration" or resource == "MedicationStatement" or resource == "MedicationRequest":
                                med_id = item["resource"]["medicationReference"]["reference"]
                                med_id = med_id[11:]
                                if med_id not in med_id_lst:
                                    med_id_lst.append(med_id)
                        print(med_id_lst)
                        

                    except KeyError:
                        msg = "Encounter ID " + enc_no[0] + " -> Requested resource (" + resource + "): No resource found"
                        self.writeLogmsg(msg)


            

        bundle = self.createBundle(res_lst, form)

        with open("tests/test.json", "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=4)
            
            

        #print(res_lst)

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
                        "meta" : { "lastUpdated" : timestring}
            }

        return bundle

    def writeLogmsg(self, msg):
        with open(self.logpath, "a") as f:
            f.writelines(msg + "\n")









if __name__ == "__main__":
    logpath = r"log.txt"
    fhirbase = r"https://mii-agiop-3p.life.uni-leipzig.de/fhir/"
    req_resources = [ "Encounter", "Patient", "Observation", "MedicationAdministration", "MedicationStatement", "Medication"]
    savepath = r"tests"
    enc_no = "1"
    utils = FhirUtils(fhirbase, logpath)
    utils.getRecord(enc_no, req_resources, savepath)