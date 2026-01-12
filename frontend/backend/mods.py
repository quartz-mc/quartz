import requests,urllib.request,json,os
import backend.debug as d
from backend.exceptions import *

API_MODRINTH = "https://api.modrinth.com/v2"

LOADER_MAP = {
    "vanilla": "vanilla",
    "fabric": "fabric",
    "lexforge": "forge",
    "neoforge": "neoforge",
    "quilt": "quilt",
    "babric":"babric",
    "bta":"bta",
    "java agent":"java-agent",
    "legacy fabric":"legacy-fabric",
    "liteloader":"liteloader",
    "risugami's modloader":"risugami",
    "nilloader":"nilloader",
    "ornithe":"ornithe",
    "rift":"rift"
}

class Mod:
    def __init__(self,id,versionId,displayName=None,displayVersion=None,description=None,gameVersion=None,modLoader=None,prerelease=False,enabled=True,fillNull=True,iconUrl=None):
        self.id = id
        self.versionId = versionId
        self.gameVersion = gameVersion
        self.modLoader = modLoader
        self.url = f"https://modrinth.com/mod/{id}"
        self.api = {
            "project":f"{API_MODRINTH}/project/{id}",
            "versions":f"{API_MODRINTH}/project/%s/version",
            "version":f"{API_MODRINTH}/version/{versionId}",
        }
        self.myProject = None
        self.myVersion = None
        self.displayName = displayName
        self.displayVersion = displayVersion
        self.description = description
        self.iconUrl = iconUrl
        self.prerelease = prerelease
        self.enabled = enabled
        if fillNull: self.fillNullData()
    def download(self,result,mandateVersion=None,mandateLoader=None):
        print(f"- {self.id}")
        r = requests.get(self.api["versions"] % self.id)
        if r.status_code == 200:
            js = r.json()
        else:
            print("  ...skipped... (couldn't find mod)")
            return 1
        for version in js:
            if version["id"] == self.versionId:
                if mandateVersion and not mandateVersion in version["game_versions"]:
                    print(f"  ...skipped... (version mismatch; {version['game_versions']} vs requested {mandateVersion})")
                    return 2
                if mandateLoader and not mandateLoader in version["loaders"]:
                    print(f"  ...skipped... (loader mismatch; {version['loaders']} vs requested {mandateLoader})")
                    return 2
                for file in version["files"]:
                    if file["primary"] == True:
                        modPath = os.path.join(result,file["filename"])
                        fileEnabled = os.path.exists(modPath)
                        fileDisabled = os.path.exists(modPath + ".disabled")
                        if not fileEnabled and fileDisabled: modPath += ".disabled"
                        if fileEnabled and self.enabled:
                            print("  ...skipped... (exists)")
                            continue # nothing needs to change
                        if not fileEnabled and not self.enabled:
                            print("  ...skipped... (disabled)")
                            continue # nothing needs to change
                        if fileEnabled and not self.enabled:
                            os.rename(modPath,modPath + ".disabled")
                            print("  ...disabled...")
                            continue
                        if not fileEnabled and self.enabled:
                            if fileDisabled:
                                print("  ...enabled...")
                                enabledName = modPath.split(".disabled")
                                if enabledName[-1] == "":
                                    enabledName.pop()
                                    enabledName = ".disabled".join(enabledName)
                                    os.rename(modPath,enabledName)
                            else:
                                print("  ...downloading...")
                                urllib.request.urlretrieve(file["url"],modPath)
                            continue
                        raise IllegalStateError("Parsed all states without consuming.")
            else:
                continue
        print("  ...skipped... (couldn't find matching version)")
        return 2
    def serialize(self):
        return [self.id,self.versionId,self.displayName,self.displayVersion,self.description,self.gameVersion,self.modLoader,self.prerelease,self.enabled]
    def fetchDependencies(self):
        r = requests.get(self.api["version"])
        if r.status_code == 200:
            js = r.json()
        else:
            return 1
        deps = js["dependencies"]
        ret = []
        for ver in deps:
            ret += [Mod(ver["project_id"],ver["version_id"])]
            ret[-1].replaceNullVersion()
        return ret
    def fillNullData(self):
        print(f"Filling null data of {self.id}")
        if not self.displayVersion:
            r = requests.get(self.api["versions"] % self.id)
            if r.status_code == 200:
                versions = r.json()
            elif r.status_code >= 400:
                d.err(r.json())
                return 1
            else:
                d.warn(r.json())
                return 1
            
            versionsPerType = {
                "release":[],
                "beta":[],
                "alpha":[]
            }
            self.myVersion = None
            if self.versionId == None:
                for version in versions:
                    if self.gameVersion in version["game_version"] and self.modLoader in version["loaders"]:
                        versionsPerType[version["version_type"]] += [version]
                for k,v in versionsPerType.items():
                    if len(v) > 0:
                        self.myVersion = v[0]
                        if k != "release":
                            d.warn("Non-release version selected.")
                            self.prerelease = True
                        break
            for version in versions:
                if self.versionId == version["id"]:
                    if self.myVersion == None:
                        self.myVersion = version
                    self.displayVersion = self.myVersion["version_number"]
        
        if not self.displayName or not self.description:
            if not self.myProject:
                r = requests.get(self.api["project"])
                self.myProject = r.json()
            self.displayName = self.myProject["title"]
            self.description = self.myProject["description"]
        
        # if self.versionId == None:
        #     r = requests.get(self.api["version"])
        #     if r.status_code == 200:
        #         js = r.json()
        #     else:
        #         d.err(r.json)
        #         return 1
        #     for version in js:
        #         if self.gameVersion in version["game_version"] and \
        #             self.modLoader in version["loaders"]:
        #             types[version["version_type"]] += [version]
        #     d.debug(types)
        #     for k,v in types.items():
        #         if len(v) > 0:
        #             self.versionId = types["release"][0]["id"]
        #             if k != "release":
        #                 d.warn("I had to pick a pre-release version as the latest version because no matching release versions were present.")
        #             break