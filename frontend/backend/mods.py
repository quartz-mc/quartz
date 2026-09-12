# new mods.py
import requests,urllib.request,json,os,datetime
from backend.exceptions import *
from backend.api import *
from backend import debug
from concurrent.futures import ThreadPoolExecutor,Future

downloadPool = ThreadPoolExecutor(8)

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

def versionManyMods(mods:list[Mod]):
    _vr = apiGet(f"{API_MODRINTH}/versions",{
        "ids":json.dumps([x.versionId for x in mods if x.myVersion == None])
    })
    _vr.raise_for_status()
    versions = _vr.json()
    for ver in versions:
        matches = [x for x in mods if x.versionId in [ver["id"]] and x.myVersion == None]
        if len(matches) > 1:
            debug.err(matches)
            raise IllegalStateError("More than one match.")
        elif len(matches) == 0:
            debug.err(matches)
            raise IllegalStateError("No matches.")
        matches[0].myVersion = ver
        matches[0].fillNullDataFromVersion()

def projectManyMods(mods:list[Mod]):
    _pr = apiGet(f"{API_MODRINTH}/projects",{
        "ids":json.dumps([x.id for x in mods if x.myProject == None])
    })
    _pr.raise_for_status()
    projects = _pr.json()
    for proj in projects:
        matches = [x for x in mods if x.id in [proj["id"],proj["slug"]] and x.myProject == None]
        if len(matches) > 1:
            debug.err(matches)
            raise IllegalStateError("More than one match.")
        elif len(matches) == 0:
            debug.err(matches)
            raise IllegalStateError("No matches.")
        matches[0].myProject = proj
        matches[0].fillNullDataFromProject()
def downloadManyMods(mods:list[Mod],result):
    ct = len(mods)
    plur = "s" if ct != 1 else ""
    debug.info(f"Versioning {ct} mod{plur}...")
    versionManyMods(mods)
    futures:list[Future] = []
    debug.info("Submitting download requests...")
    for m in mods:
        futures += [downloadPool.submit(m.downloadFromVersion,result)]
    debug.info("Waiting for downloads to complete...")
    for f in futures:
        f.result()
    debug.info("Done!")

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
            "version":f"{API_MODRINTH}/version/%s",
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
    @classmethod
    def fromURL(cls,url,fillNull=True):
        lightweight = url.replace("https","http").replace("http://","").split("/") # cdn.modrinth.com/data/m5T5xmUy/versions/r4yqxYQl/BetterGrassify-1.8.7%2Bfabric.26.2.jar
        if not lightweight[0] == "cdn.modrinth.com":
            raise UnsupportedModSource(f"Only modrinth mods are supported. (failed to fetch mod from url '{url}')")
        i = 0
        id = ""
        versionId = ""
        while i < len(lightweight):
            v = lightweight[i]
            if v == "data":
                i += 1
                id = lightweight[i]
            elif v == "versions":
                i += 1
                versionId = lightweight[i]
            i += 1
        self = Mod(id,versionId,"","","","","",False,True,False,None)
        if fillNull: self.fillNullData()
        return self
    def fillNullVersion(self,mandateVersion=None,mandateLoader=None,lockVersionId=True):
        if not self.myVersion:
            r = apiGet(self.api["versions"] % self.id)
            if r.status_code >= 300:
                debug.warn("  ...skipped... (couldn't find mod)")
                debug.warn(r.status_code)
                # debug.warn(r.text)
                return 1
            js = r.json()
            matches = js
            if lockVersionId: matches = [x for x in matches if x["id"] == self.versionId]
            if mandateVersion: matches = [x for x in matches if mandateVersion in x["game_versions"]]
            if mandateLoader: matches = [x for x in matches if mandateLoader in x["loaders"]]
            if len(matches) == 0:
                debug.warn(f"  ...skipped... (no versions found)")
                return 1
            self.myVersion = matches[0]
            debug.warn(matches)
        return 0
    def downloadFromVersion(self,result):
        if self.myVersion == None:
            raise IllegalStateError("self.myVersion is None.")
        print(f"- Downloading {self.id}")
        primaryFiles = [x for x in self.myVersion["files"] if x["primary"] == True]
        if len(primaryFiles) == 0:
            raise MissingModSource("Mod has no primary file.")
        file = primaryFiles[0]
        modPath:str = os.path.join(result,file["filename"])
        isEnabled = os.path.exists(modPath)
        isDisabled = os.path.exists(modPath + ".disabled")
        if not isEnabled and isDisabled: modPath += ".disabled"
        if isEnabled and isDisabled: raise IllegalStateError("Mod is both disabled and enabled.")
        if isEnabled and self.enabled:
            print("  ...skipped... (exists)")
            return 2
        elif isDisabled and not self.enabled:
            print("  ...skipped... (disabled)")
            return 2
        elif isEnabled and not self.enabled:
            os.rename(modPath,modPath + ".disabled")
            print("  ...enabled...")
            return 2
        elif isDisabled and self.enabled:
            enabledName = modPath.rsplit(".disabled",maxsplit=1)[0]
            os.rename(modPath,enabledName)
            return 2
        elif not isEnabled and not isDisabled and self.enabled:
            print("  ...downloading...")
            urllib.request.urlretrieve(file["url"],modPath)
            return 2
        else:
            raise IllegalStateError("All valid states reached without consuming.")
    def download(self,result,mandateVersion=None,mandateLoader=None,lockVersionId=True):
        if (self.fillNullVersion(mandateVersion,mandateLoader,lockVersionId) != 0): return 1
        # debug.debug(self.myVersion)
        # return 2
        return self.downloadFromVersion(result)
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
        r = apiGet(self.api["version"] % self.versionId)
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
    def fillNullDataFromVersion(self):
        self.displayVersion = self.myVersion["version_number"]
        self.prerelease = self.myVersion["version_type"] != "release"
    def fillNullDataFromProject(self):
        self.displayName = self.myProject["title"]
        self.description = self.myProject["description"]
        self.iconUrl = self.myProject["icon_url"]
    def fillNullData(self):
        print(f"Filling null data of {self.id}")
        if not self.displayVersion:
            if not self.versionId or not self.myVersion:
                # get the latest version
                query = {}
                if self.modLoader:
                    query["loaders"] = [self.modLoader]
                if self.gameVersion:
                    query["game_versions"] = [self.gameVersion]
                r = apiGet(self.api["versions"] % self.id,query)
                r.raise_for_status()

                versions = r.json()

                releases = []
                self.prerelease = False
                for type in ["release","beta","alpha"]:
                    releases = [x for x in versions if x["version_type"] == type]
                    if len(releases) != 0: break
                    self.prerelease = True
                else:
                    raise NoReleases("Mod has no releases.")
                releases.sort(key=lambda a : datetime.datetime.fromisoformat(a["date_published"]).timestamp(),reverse=True)
                self.myVersion = r.json(releases[0])
            self.fillNullDataFromVersion()
        if not self.displayName:
            if not self.id:
                raise IllegalStateError("Mod with no ID!")
            r = apiGet(self.api["project"])
            r.raise_for_status()

            self.myProject = r.json()
            self.fillNullDataFromProject()

        # NOTE: the following code is SO ass, please never use it.
        # if not self.displayVersion:
        #     if not self.versionId:
        #         r = apiGet(self.api["versions"] % self.id)
        #         if r.status_code == 200:
        #             versions = r.json()
        #         elif r.status_code >= 400:
        #             d.err(r.text)
        #             d.err(f"status code: {r.status_code}")
        #             return 1
        #         else:
        #             d.warn(r.text)
        #             d.err(f"status code: {r.status_code}")
        #             return 1
                
        #         versionsPerType = {
        #             "release":[],
        #             "beta":[],
        #             "alpha":[]
        #         }
        #         self.myVersion = None
        #         if self.versionId == None:
        #             for version in versions:
        #                 if self.gameVersion in version["game_version"] and self.modLoader in version["loaders"]:
        #                     versionsPerType[version["version_type"]] += [version]
        #             for k,v in versionsPerType.items():
        #                 if len(v) > 0:
        #                     self.myVersion = v[0]
        #                     if k != "release":
        #                         d.warn("Non-release version selected.")
        #                         self.prerelease = True
        #                     break
        #         for version in versions:
        #             if self.versionId == version["id"]:
        #                 if self.myVersion == None:
        #                     self.myVersion = version
        #                 self.displayVersion = self.myVersion["version_number"]
        #     else:
        #         r = apiGet
        
        # if not self.displayName or not self.description:
        #     if not self.myProject:
        #         r = apiGet(self.api["project"])
        #         self.myProject = r.json()
        #     self.displayName = self.myProject["title"]
        #     self.description = self.myProject["description"]
        
        # if self.versionId == None:
        #     r = apiGet(self.api["version"] % self.versionId)
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