from fhirutils import loader

if __name__ == "__main__":
    logpath = r"log.txt"
    #fhirbase = r"http://10.50.8.14:8080/fhir/_/"
    fhirbase = r"https://mii-agiop-3p.life.uni-leipzig.de/fhir/"
    req_resources = [ "Encounter", "Patient", "MedicationStatement", "Medication"]
    savepath = r"C:\\Users\\brandesju\\Documents\\ressourcen_neu"
    config_path = r"V:\\Eigene Dateien\\Kerndatensatz\\fhirutils\\config.json"
    profile = "KDS"

    loader = loader.Loader(fhirbase=fhirbase, logpath=logpath)
        
    encounters = ["1", "439", "UKB003E-1"]
    # with open("encounters.csv", "r") as f:
    #     reader = csv.reader(f)
    #     for item in reader:
    #         encounters.append(item[0])

    print(encounters)

    for enc in encounters:
        destinationfile = enc + ".json"
        enc_no = enc
        loader.getRecord(enc_no, req_resources, savepath, destinationfile, config_path, profile)