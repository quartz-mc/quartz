import os
import json
import copy
from backend import version
def createInstance(instances,mcVersion,name="Untitled",loader=""):
    newInstance = {
        "format":version.QUARTZ_JSON_LATEST,
        "path":None,
        "name":"Untitled",
        "version":mcVersion,
        "loader":"",
        "mods":[],
        "rootSkipped":[]
    }
    instances += [newInstance]
    return newInstance

def saveInstance(inst):
    oldMods = inst["mods"]
    inst["mods"] = [x.serialize() for x in inst["mods"]]

    if inst["path"] == None:
        inst["path"] = "instances/" + "".join([x.replace(" ","-").lower() for x in inst["name"] if x.isalnum() or x in "- "])
    path = inst["path"]
    if path.endswith(".json"):
        os.makedirs(os.path.dirname(path),exist_ok=True)
        jsonPath = path
    else:
        os.makedirs(path,exist_ok=True)
        jsonPath = os.path.join(path,"quartz.json")
    with open(jsonPath,"w") as f:
        json.dump(inst,f)
    inst["mods"] = oldMods