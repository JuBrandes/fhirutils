import pandas as pd
import requests
import json


class Utils():
    def __init__(self, logpath=None):
        self.logpath = logpath
        self.errorstatus = False
        if self.logpath is not None:
            with open(self.logpath, "w") as _:
                pass

        self.format_dict = {
                "json": "&_format=json",
                "xml": "&_format=xml"
            }

    def get(self, i=None, s=None, t="url", f="json"):
        """
        returns a data item from a FHIR-resource/bundle by given json-path

        args:
            i: item via json path, e.g.: "entry.0.resource.status"
            s: source, can be a url, a local file or a bundle
            t: the source's type, "url" (default), "local" or "bundle"
            f: format of loaded resource/bundle, "json" (default) or "xml" (not yet implemented!)

        returns:
            tuple: (path, result)
        """

        json_data = None
        if t == "url":
            search_url = s + self.format_dict[f]
            print(search_url)
            req = requests.get(search_url)
            downloads = str(req.content, encoding='cp1252')
            if f == "json":
                json_data = json.loads(downloads)

        elif t == "local":
            with open(s, "r") as source:
                json_data = json.loads(source.read())

        elif t == "resource":
            json_data = s

        result_value = self.find_by_path(i, json_data)

        return result_value

    def find_by_path(self, element, data):
        path = element.split(".")
        subpath = path.copy()
        d = data
        for item in path:
            subpath.remove(item)
            try:
                item = int(item)
            except ValueError:
                pass
            if item == "X":
                ret_lst = []
                length = len(d)
                if length == 1:
                    length = 2
                for i in range(length-1):
                    if i < 0:
                        i = 0
                    keyerror = False
                    sub_d = d.copy()
                    sub_d = sub_d[i]
                    for subitem in subpath:
                        try:
                            sub_d = sub_d[subitem]
                        except KeyError:
                            keyerror = True
                    if not keyerror:
                        path_copy = None
                        for j in range(len(path)):
                            if path[j] == "X":
                                path_copy = path.copy()
                                path_copy[j] = str(i)
                                path_copy = ".".join(path_copy)
                        ret_lst.append([path_copy, sub_d])

                df = pd.DataFrame(ret_lst)
                print(ret_lst)
                df.columns = ["path", "value"]
                return df

            try:
                d = d[item]
            except TypeError:
                pass
            except KeyError:
                pass

        df = pd.DataFrame([element, d]).T
        df.columns = ["path", "value"]

        return df


if __name__ == "__main__":
    util = Utils()
    s = r"https://mii-agiop-3p.life.uni-leipzig.de/fhir/Patient?_count=200"
    t = "url"
    i = "entry.X.resource"
    print(util.get(i=i, s=s, t=t))
