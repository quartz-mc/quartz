import platformdirs,pathlib,json

_open = open

configDir = pathlib.Path(platformdirs.user_config_dir(appname="quartz-launcher",ensure_exists=True))

def getPath(where) -> pathlib.Path:
    return configDir / where
def ensureDir(path:pathlib.Path):
    path.mkdir(parents=True,exist_ok=True)
def ensureParent(path:pathlib.Path):
    ensureDir(path.parent)
def doesPathExist(where):
    p = getPath(where)
    ensureParent(p)
    return getPath(where).exists()
def open(where,mode="r"):
    p = getPath(where)
    ensureParent(p.parent)
    return _open(p,mode)

configDefaults = {}

def configRegister(where:str,key:str,value):
    if not where in configDefaults:
        configDefaults[where] = {}
    configDefaults[where][key] = value

def configLoad(where:str):
    try:
        with open(where,"r") as f:
            j:dict = json.load(f)
    except:
        j:dict = {}
    if not isinstance(j,dict): return configDefaults.get(where,{})
    j.update(configDefaults.get(where,{}))
    return j

def configSave(where:str,conf:dict):
    with open(where,"w") as f:
        json.dump(conf,f)