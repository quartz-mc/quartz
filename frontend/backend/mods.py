import requests,urllib.request,json,os
import backend.debug as d

API_MODRINTH = "https://api.modrinth.com/v2"

class Mod:
    def __init__(self,id,versionId,gameVersion=None,modLoader=None,local=False):
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
    def download(self,result):
        r = requests.get(self.api["versions"] % self.id)
        if r.status_code == 200:
            js = r.json()
        else:
            return 1
        for version in js:
            if version["id"] == self.versionId:
                for file in version["files"]:
                    if file["primary"] == True:
                        urllib.request.urlretrieve(file["url"],os.path.join(result,file["filename"]))
                        return 0
            else:
                continue
        return 2
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
    def replaceNullVersion(self):
        if self.versionId == None:
            r = requests.get(self.api["version"])
            if r.status_code == 200:
                js = r.json()
            else:
                print(r.json)
                return 1
            types = {
                "release":[],
                "beta":[],
                "alpha":[]
            }
            for version in js:
                if self.gameVersion in version["game_version"] and \
                    self.modLoader in version["loaders"]:
                    types[version["version_type"]] += [version]
            d.debug(types)
            for k,v in types.items():
                if len(v) > 0:
                    self.versionId = types["release"][0]["id"]
                    if k != "release":
                        d.warn("I had to pick a pre-release version as the latest version because no matching release versions were present.")
                    break