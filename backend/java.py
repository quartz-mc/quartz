from . import brand
import platform,os

class ClassPath:
    def __init__(self,lib,jar):
        self.lib = lib
        self.jar = jar
        self.comb = os.pathsep
    def serialize(self):
        return self.lib + self.comb + self.jar

class Memory:
    def __init__(self,javaNatives,startingHeap=512,maximumHeap=2048,memoryAllocator=":+UseG1GC",brand=brand.Brand("Unknown","0.0"),
                 classPath=None,instance=None,credentials=None

                 extraCommandlineArgs=""):
        self.offline = credentials == None
        self.Xms = startingHeap
        self.Xmx = maximumHeap
        self.XX = memoryAllocator
        self.DNatives = javaNatives # -Djava.library.path=/path/to/natives
        self.DLauncherBrand = brand.brand
        self.DLauncherVersion = brand.version
        
        self.ClassPath = classPath.serialize()

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