import backend.brand as brand
import os
import subprocess
import backend.assets as _assets
import requests
import platform
import urllib.request
import zipfile
import tarfile

os.makedirs("backend/java",exist_ok=True)

class JavaSource:
    ADOPTIUM = 0
    ORACLE = 1

def getJava(feature_version,jsrc=JavaSource.ADOPTIUM):
    os.makedirs("java",exist_ok=True)
    if os.path.exists(f"java/{feature_version}"): return ["warn","Exists"]
    print("\n# Getting Java...\n")
    match jsrc:
        case JavaSource.ADOPTIUM:
            system = platform.system().lower()
            if system == "darwin": system = "mac"
            if system == "java": raise SystemError("Jython is not supported, as it does not give meaningful platform.system() information.")
            machine = platform.machine().lower()
            machine = machine.replace("x86_64","x64")
            machine = machine.replace("i386","x86")
            machine = machine.replace("i686","x86")
            if machine.startswith("arm"): machine = "arm"
            if not machine in ["x64","x86","arm","aarch64","ppc64","ppc64le","s390x","sparc64","riscv64"]: return ["fail",f"Adoptium does not support {machine}"]
            url = f"https://api.adoptium.net/v3/assets/latest/{feature_version}/hotspot"
            r = requests.get(url,{"architecture":platform.machine(),"image_type":"jre","os":system,"vendor":"eclipse"})
            if r.status_code == 200:
                print("- Got ADOPTIUM source.")
                r = r.json()
                url = r[0]["binary"]["package"]["link"]
                os.makedirs("/tmp/quartz/java",exist_ok=True)
                urllib.request.urlretrieve(url,f"/tmp/quartz/java/archive")
                """
                the above retrieved file is a:
                .tar.gz on linux and mac,
                and .zip on windows."""
                topmost = "/tmp/quartz/java/" + os.listdir("/tmp/quartz/java")[0]
                if zipfile.is_zipfile(topmost):
                    with zipfile.ZipFile(topmost,"r") as f:
                        os.makedirs(f"java/{feature_version}/",exist_ok=True)
                        f.extractall(f"java/{feature_version}/")
                elif tarfile.is_tarfile(topmost):
                    with tarfile.open(topmost,"r:*") as f:
                        os.makedirs(f"java/{feature_version}/",exist_ok=True)
                        f.extractall(f"java/{feature_version}/")
                else:
                    return ["fail","Bad archive."]
                if len(os.listdir(f"java/{feature_version}")) == 1:
                    os.rename(f"java/{feature_version}","java/_")
                    os.rename(os.path.join(f"java/_",os.listdir(f"java/_")[0]),f"java/{feature_version}")
                    os.rmdir("java/_")
            else:
                return ["fail","Request failed."]
        case _:
            print("- Illegal JavaSource passed.")

class Assets:
    def __init__(self,path,index):
        self.path = path
        self.index = index

class Instance:
    def __init__(self,version,versionType,path,assets,entrypoint):
        self.version = version
        self.versionType = versionType
        self.path = path
        self.assets = assets
        self.entrypoint = entrypoint

class ExtraArgs:
    def __init__(self,java,mc):
        self.java = java
        self.mc = mc

class ClassPath:
    def __init__(self,libDir,jar):
        self.comb = os.pathsep
        self.libDir = libDir
        self.expandGlob()
        self.jar = jar
    def expandGlob(self):
        jars = []
        for root,_,files in os.walk(self.libDir):
            for f in files:
                if f.endswith(".jar"):
                    jars.append(os.path.join(root,f))
        self.lib = self.comb.join(jars)
    def serialize(self):
        return self.lib + self.comb + self.jar

class Memory:
    def __init__(self,startingHeap=512,maximumHeap=2048,memoryAllocator="+UseG1GC"):
        self.Xms = startingHeap
        self.Xmx = maximumHeap
        self.XX = memoryAllocator

class Runner:
    def __init__(self,javaExecutable,javaNatives,memory=None,brand=brand.Brand("Unknown","Unknown"),
                    classPath=None,instance=None,credentials=None,
                    
                    extraCommandlineArgs=""):
        self.exec = javaExecutable

        self.offline = credentials == None
        self.Xms = memory.Xms
        self.Xmx = memory.Xmx
        self.XX = memory.XX
        self.DNatives = javaNatives # -Djava.library.path=/path/to/natives
        self.DLauncherBrand = brand.brand
        self.DLauncherVersion = brand.version
        
        self.ClassPath = classPath.serialize()

        self.entrypoint = instance.entrypoint

        self.username = credentials.username
        self.uuid = credentials.uuid
        self.accessToken = credentials.accessToken
        self.userType = credentials.userType

        self.version = instance.version
        self.versionType = instance.versionType
        self.gameDir = instance.path
        self.assetsDir = instance.assets.path
        self.assetIndex = instance.assets.index

        self.extraJava = extraCommandlineArgs.java
        self.extraAuth = credentials.extras # for clientId and xuid

        self.extraMine = extraCommandlineArgs.mc
    def run(self):
        credentials = ["--username",self.username,"--uuid",self.uuid,"--accessToken",self.accessToken,"--userType",self.userType]
        runLine = f"""{self.exec} -Xms{self.Xms}M -Xmx{self.Xmx}M -XX:{self.XX} -Djava.library.path="{self.DNatives}"
{self.extraJava}
-Dminecraft.launcher.brand={self.DLauncherBrand} -Dminecraft.launcher.version={self.DLauncherVersion}
-cp "{self.ClassPath}" {self.entrypoint} {credentials} --version {self.version} --gameDir {self.gameDir} --assetsDir {self.assetsDir} --assetIndex {self.assetIndex}
{self.extraMine} {self.extraAuth}""".replace("\n"," ")
        args = [
            self.exec,f"-Xms{self.Xms}M",f"-Xmx{self.Xmx}M",f"-XX:{self.XX}",f"-Djava.library.path={self.DNatives}",*self.extraJava,
            f"-Dminecraft.launcher.brand={self.DLauncherBrand}",f"-Dminecraft.launcher.version={self.DLauncherVersion}",
            f"-cp",f"{self.ClassPath}",self.entrypoint,*credentials,"--version",self.version,"--gameDir",self.gameDir,"--assetsDir",
            self.assetsDir,"--assetIndex",self.assetIndex,self.extraMine,self.extraAuth
        ]
        args = [x for x in args if x != ""]
        print(args)
        rcode = subprocess.call(args)
        return rcode,args

if __name__ == "__main__":
    import auth,version
    versions = version.get()
    versionsDict = {x.id:x for x in versions}
    thisVer = versionsDict["1.21.11"]
    versionId = thisVer.id
    versionType = thisVer.type
    json = version.download(f"versions/{versionId}/",version=thisVer,type="json",modloader=version.Modloaders.FABRIC,modloaderVersion={"loader":"0.18.4"})
    assets = { # this is all the info i need.
        "id":json["assetIndex"]["id"],
        "sha1":json["assetIndex"]["sha1"]
    }
    version.download(f"assets/indexes/",json=json,type="assetIndex",sha1=assets["sha1"])
    _assets.download(f"assets/objects",f"assets/indexes/{assets['id']}.json")
    version.download(f"versions/{versionId}/",json=json,type="jar",modloader=version.Modloaders.FABRIC,modloaderVersion={"loader":"0.18.4"})
    version.download(f"versions/{versionId}/natives",json=json,type="natives")
    version.download(f"libraries",json=json,type="libraries")
    ret = getJava(JavaSource.ADOPTIUM,json["javaVersion"]["majorVersion"])
    print(ret)
    javas = os.listdir("java")
    javaPath = f"java/{javas[0]}/bin/java"
    r = Runner(javaPath,f"versions/{versionId}/natives",Memory(512,2048),brand.Brand("Quartz","1.0.0"),ClassPath("libraries/",f"versions/{versionId}/client.jar"),
               Instance(versionId,versionType,"instances/demo",Assets("assets/",f"{assets['id']}"),json["mainClass"]),auth.offline("quartz_dev"),
               ExtraArgs("",""))
    rc,args = r.run()
    print(f"\n\n\nGame exited with return code {rc}")
    print(f"Game was invoked with args {args}")