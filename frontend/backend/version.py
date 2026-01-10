from enum import Enum
import requests,re,urllib.request,zipfile,os,hashlib,platform,pathlib
import json as js
import copy
from backend.debug import *

def jsonInherit(base,child):
    result = copy.deepcopy(base)
    for key in child:
        if not key in result:
            result[key] = child[key]
            continue
        baseValue = result[key]
        childValue = child[key]
        if isinstance(baseValue,dict) and isinstance(childValue,dict):
            result[key] = jsonInherit(baseValue,childValue)
        elif isinstance(baseValue,list) and isinstance(childValue,list):
            result[key] = baseValue + childValue
        else:
            result[key] = childValue
    return result

def pathGetOnlyChild(path):
    dir = os.listdir(path)
    if len(dir) != 1:
        raise OSError(f"The number of children of path {path} is not 1.")
    return os.path.join(path,dir[0])

def jsonInheritance(path):
    with open(path,"r") as f:
        child = js.load(f)
    if "inheritsFrom" not in child:
        return
    parent_id = child["inheritsFrom"]
    os.makedirs("/tmp/quartz/inheritance/",exist_ok=True)
    versions = get()
    versionsDict = {x.id:x for x in versions}
    parentVer = versionsDict[parent_id]
    download("/tmp/quartz/inheritance/","json",version=parentVer,modloader=Modloaders.VANILLA)
    with open(pathGetOnlyChild("/tmp/quartz/inheritance/"),"r") as f:
        parent = js.load(f)
    if "inheritsFrom" in parent:
        warn("Inheritance is incomplete; parent has an inheritance.")
    with open(path,"w") as f:
        json = jsonInherit(parent,child)
        js.dump(json,f)
    print("Inheritance completed.")

class Modloaders(Enum):
    VANILLA = 1
    """
    Unmodified minecraft directly from mojang.
    """

    FABRIC = 2
    """
    The Fabric Modloader found at https://fabricmc.net
    """

    NEOFORGE = 3
    """
    The NeoForge Modloader, which forked from Forge in 2023, found at https://neoforged.net/
    
    This is preferred over LexForge, however LexForge is still supported.
    """

    FORGE = 4
    """
    The Forge Modloader which is stupid and yucky.

    Provides a warning if a version released after July 12th 2023 is used.
    Referred to as LexForge for all versions released after July 12th 2023.
    """

class ChecksumError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class Version:
    def __init__(self,id,type,jsonUrl,time,releaseTime):
        self.id = id
        self.type = type
        self.json = jsonUrl
        self.time = time
        self.releaseTime = releaseTime

def getMojangOS():
    sys = platform.system().lower()
    mch = platform.machine().lower()
    match sys:
        case "linux":
            return "linux"
        case "windows":
            return "windows"
        case "java":
            raise SystemError("Dunno what system this is. Don't use Jython.")
        case "darwin":
            if mch in ("arm64","aarch64"):
                return "osx-arm64"
            else:
                return "osx"
        case _:
            raise SystemError("I don't recognize your operating system. Linux, Windows, and MacOS are supported.")

def fsha1(path):
    sha = hashlib.sha1()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(8192),b""):
            sha.update(chunk)
    return sha.hexdigest()

def get(url="https://launchermeta.mojang.com/mc/game/version_manifest.json"):
    response = requests.get(url)
    if str(response.status_code)[0] == "2":
        json = response.json()
    else:
        return None
    jsonversions = json["versions"]
    versions = []
    for ver in jsonversions:
        versions.append(Version(ver["id"],ver["type"],ver["url"],ver["time"],ver["releaseTime"]))
    return versions

def download(path,type,version=None,sha1=None,json=None,modloader=Modloaders.VANILLA,modloaderVersion={}):
    print(f"\n# Beginning downloads for download type '{type}'\n")
    os.makedirs(path,exist_ok=True)
    match type:
        case "json":
            match modloader:
                case Modloaders.VANILLA:
                    urls = [version.json]
                case Modloaders.FABRIC:
                    urls = [f"https://meta.fabricmc.net/v2/versions/loader/{version.id}/{modloaderVersion['loader']}/profile/json"]
        case "jar":
            match modloader:
                case Modloaders.VANILLA:
                    if "mainJar" in json.keys():
                        urls = [json["mainJar"]["downloads"]["artifact"]["url"]]
                    else:
                        urls = [json["downloads"]["client"]["url"]]
                case Modloaders.FABRIC:
                    urls = []
                case _:
                    raise NotImplementedError(f"Mod loader {modloader} not implemented.")
        case "assetIndex":
            urls = [json["assetIndex"]["url"]]
        case "natives":
            _urls = [x for x in json["libraries"] if re.search("[:-]natives?-",x["name"])]
            urls = []
            for url in _urls:
                permit = False
                if not "rules" in url.keys():
                    permit = True
                else:
                    for rule in url["rules"]:
                        if rule["os"]["name"] != getMojangOS(): continue
                        if rule["action"] == "allow":
                            permit = True
                        if rule["action"] == "disallow":
                            permit = False
                if permit:
                    urls += [url]
            urls = [x["downloads"]["artifact"]["url"] for x in urls if x]
        case "libraries":
            urls = []
            for x in json["libraries"]:
                if re.search("[:-]natives-",x["name"]): continue
                if "downloads" in x:
                    urls.append(x["downloads"]["artifact"]["url"])
                else:
                    name = x["name"]
                    group,artifact,version = name.split(":")

                    urls.append("/".join([
                        x["url"],
                        group.replace(".","/"),
                        artifact,
                        version,
                        f"{artifact}-{version}.jar"
                    ]))
    results = []
    modified = []
    for url in urls:
        print(f"- Downloading from {url}")
        if type == "json":
            name = version.id
            if modloader != Modloaders.VANILLA:
                name += f"-" + modloader.name.lower() + ".json"
        else:
            name = os.path.basename(url)
        truepath = os.path.join(path, name)
        results += [truepath]
        if os.path.exists(truepath):
            print("  ...skipped...")
            continue
        modified += [truepath]
        urllib.request.urlretrieve(url,truepath)
    if type == "json":
        if sha1:
            if fsha1(results[0]) != sha1:
                raise 
        with open(results[0],"r") as f:
            ret = js.load(f)
        newPath = os.path.join(os.path.split(results[0])[0],ret["id"]) + ".json"
        os.rename(results[0],newPath)
        results[0] = newPath
        if "inheritsFrom" in ret:
            jsonInheritance(results[0])
        with open(results[0],"r") as f:
            ret = js.load(f)
        return ret
    elif type == "natives":
        for result in modified:
            with zipfile.ZipFile(result,"r") as jar:
                for lib in jar.namelist():
                    if lib.endswith((".so",".dll",".dylib")):
                        jar.extract(lib,path)
            if result: os.remove(result)
    return results # i'm not using this but if someone for some reason uses this as a library, here's the results