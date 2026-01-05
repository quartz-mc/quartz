import requests,re,urllib.request,zipfile,os,hashlib,platform,pathlib
import json as js

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

def download(path,type,version=None,sha1=None,json=None):
    print(f"\n# Beginning downloads for download type '{type}'\n")
    os.makedirs(path,exist_ok=True)
    match type:
        case "json":
            urls = [version.json]
        case "jar":
            if "mainJar" in json.keys():
                urls = [json["mainJar"]["downloads"]["artifact"]["url"]]
            else:
                urls = [json["downloads"]["client"]["url"]]
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
            urls = [x["downloads"]["artifact"]["url"] for x in json["libraries"] if not re.search("[:-]natives?-",x["name"])]
    results = []
    modified = []
    for url in urls:
        print(f"- Downloading from {url}")
        truepath = os.path.join(path, os.path.basename(url))
        results += [truepath]
        if os.path.exists(truepath): continue
        modified += [truepath]
        urllib.request.urlretrieve(url,truepath)
    if type == "json":
        if sha1:
            if fsha1(results[0]) != sha1:
                raise 
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
    return results # i'm not using this but if someone for some reason uses this as a library, sure, here's the results