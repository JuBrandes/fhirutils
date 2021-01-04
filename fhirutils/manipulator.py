import requests
import json

class Manipulator():
    def __init__(self, logpath=None):
        self.logpath = logpath
        self.errorstatus = False
        if self.logpath is not None:
            with open(self.logpath, "w") as f:
                pass

        self.format_dict = {
                "json" : "&_format=json",
                "xml" : "&_format=xml"
            }

    def pop(self, i=None, s=None, t="url", d=None, f="json"):
        """
        returns a data item from a FHIR-resource/bundle

        args:
            i: item, e.g.: "status"
            s: source, can be a url or a local file
            t: the source's type, "url" (default) or "local"
            d: if destination is set, the selected item will be deleted and the new resource/bundle will be saved at this filepath
            f: format of loaded resource/bundle, "json" (default) oder "xml"

        returns:
            bundle or resource according to input
        """

        if t == "url":
            search_url = s + self.format_dict[f]
            print(search_url)
            req = requests.get(search_url)
            #self.printRequestsMessage(req, search_url)
            downloads = str(req.content, encoding='cp1252')
            if f == "json":
                json_data = json.loads(downloads)
                

        elif t == "local":
            with open(s, "r") as source:
                json_data = json.loads(source.read())

        result = self.getItem(json_data, i)
    
        return list(result)[0]
        
        

    def getItem(self, data, item, delete=False, path=()):
        if isinstance(data, dict):
            for k, v in data.items():
                if k == item:
                    yield k, v
                elif isinstance(v, dict):
                    for result in self.getItem(v, item):
                        path=path + (v, )
                        yield item, result
                elif isinstance(v, list):
                    for d in v:
                        if isinstance(d, dict):
                            for result in self.getItem(d, item):
                                path=path + (v, )
                                yield item, result
      

if __name__ == "__main__":
    mani = Manipulator()
    s = r"V:\\Eigene Dateien\\Kerndatensatz\\fhirutils\\tests\\Encounter.json"
    t = "local"
    i = "resource"
    print(mani.pop(i=i, s=s, t=t)[1])

