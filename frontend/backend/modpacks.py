from backend import util,mods,exceptions,debug,api
import zipfile,json,pathlib

def fetchModrinthPack(instances,path:str):
    def mrpackOverrides(z:zipfile.ZipFile,dest,getParent=False):
        destination = pathlib.Path(dest)
        if getParent: destination = destination.parent
        files = [x for x in z.infolist() if x.filename.startswith("overrides/")]
        for f in files:
            relative = pathlib.Path(f.filename).relative_to("overrides")
            target = (destination / relative).resolve()
            if not target.is_relative_to(destination.resolve()):
                debug.warn("Potentially malicious archive, files would end up outside the instance. No overrides will be processed; configuration will be missing!")
                return
        for f in files:
            relative = pathlib.Path(f.filename).relative_to("overrides")
            target = (destination / relative).resolve()
            if f.is_dir():
                target.mkdir(parents=True,exist_ok=True)
                continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(f) as src, target.open("wb") as dest:
                dest.write(src.read())
    with zipfile.ZipFile(path,"r") as z:
        with z.open("modrinth.index.json","r") as f:
            data = json.load(f)
    if not "minecraft" in data["dependencies"]:
        raise exceptions.BadModpack("Minecraft dependency not specified.")
    instance = util.createInstance(instances,data["dependencies"]["minecraft"])
    instance["loader"] = "vanilla"
    for k,v in data["dependencies"].items():
        match k:
            case "forge":
                instance["loader"] = "Lexforge"
            case "neoforge":
                instance["loader"] = "Neoforge"
            case "fabric-loader":
                instance["loader"] = "Fabric"
            case "quilt-loader":
                instance["loader"] = "Quilt"
    instance["name"] = f"{data["name"]} ({data['versionId']})"
    for i in data["files"]:
        match i["path"].split("/")[0]:
            case "mods":
                dlErrors = []
                for dl in i["downloads"]:
                    try:
                        instance["mods"] += [mods.Mod.fromURL(dl,fillNull=False)]
                        break
                    except Exception as e:
                        dlErrors += [e]
                else:
                    if len(dlErrors) == 0:
                        raise exceptions.MissingModSource(f"No download URLs provided for mod '{i["path"]}'")
                    elif len(dlErrors) == 1:
                        raise dlErrors[0]
                    raise ExceptionGroup("None of the download URLs succeeded.",dlErrors)
            case "resourcepacks":
                debug.warn("Resource packs are not currently supported.")
    debug.info("Updating nulls (from versions...)")
    mods.versionManyMods(instance["mods"])
    debug.info("Updating nulls (from projects...)")
    mods.projectManyMods(instance["mods"])
    util.saveInstance(instance)
    with zipfile.ZipFile(path,"r") as z:
        mrpackOverrides(z,instance["path"],getParent=False)
def fetchArbitraryPack(instances,path:str):
    match path.split(".")[-1]:
        case "mrpack":
            fetchModrinthPack(instances,path)