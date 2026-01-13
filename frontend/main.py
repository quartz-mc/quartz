import dearpygui.dearpygui as dpg
import themes
import backend.mods as mods
import backend.debug as d
import backend.java
import backend.version as version
import backend.assets as _assets
import backend.brand
import backend.auth
import os
import time
import traceback
import threading
import json as js
import pathlib
import shutil
import requests
import urllib.request
from PIL import Image
from io import BytesIO
from backend.exceptions import *

def fatalErrorTxt(msg):

    with dpg.window(no_resize=True,no_move=True,label="Fatal Error!"):
        dpg.add_text("Quartz Launcher has encountered a fatal error!\n")
        dpg.add_text(msg)
        dpg.add_text("\nQuartz will close in 30 seconds.")
    for i in range(30):
        time.sleep(1)
        if not dpg.is_dearpygui_running():
            return
    dpg.stop_dearpygui()

def fatalError(exception):
    fatalErrorTxt("".join(traceback.format_exception(exception)))
    raise exception

def rebuildMods(si):
    print("\n# Rebuilding mods...\n")
    modsDir = os.path.join(si["path"],"mods")
    os.makedirs(modsDir,exist_ok=True)
    for x in si["mods"]:
        mod: mods.Mod = x
        mod.download(modsDir)
    for x in root["mods"]:
        mod: mods.Mod = x
        if mod.id in si["rootSkipped"]:
            continue
        mod.download(modsDir,mandateVersion=si["version"],mandateLoader=si["loader"].lower())

def on_instance_click(sender,app_data,user_data):
    global selectedInstance
    selectedInstance = user_data["index"]

def rebuildSearchResults(modList: list[mods.Mod]):
    if dpg.does_item_exist("ei_mod_search_results_group"):
        dpg.delete_item("ei_mod_search_results_group")
    with dpg.group(parent="ei_mod_search_results",tag="ei_mod_search_results_group"):
        for mod in modList:
            with dpg.group(horizontal=True,horizontal_spacing=10):
                dpg.add_button(width=60,height=50,label="Install",user_data=mod.serialize(),callback=si_installMod)
                with dpg.group():
                    dpg.add_text(mod.displayName,wrap=180)
                    dpg.add_text(mod.description,wrap=180)

instances_rows = []
def rebuildInstancesPane():
    if dpg.does_item_exist("instances"):
        dpg.delete_item("instances")
    width = dpg.get_item_width("left_pane")
    INST_WIDTH = 200
    INST_HEIGHT = 75
    cols = max(1,width//INST_WIDTH)
    with dpg.table(
        tag="instances",
        parent="left_pane",
        header_row=False,
        policy=dpg.mvTable_SizingFixedFit,
        borders_innerH=False,
        borders_innerV=False,
        borders_outerH=False,
        borders_outerV=False
    ):
        global instances_rows
        for row in instances_rows:
            dpg.delete_item(row)
        for _ in range(cols):
            dpg.add_table_column()
        col = 0
        instances_rows = [dpg.add_table_row(tag="table_row_1")]
        rows = 1
        for i,instance in enumerate(instances):
            dpg.add_button(
                tag=f"instance_button_{i}",
                parent=instances_rows[-1],
                label=instance["name"],
                width=INST_WIDTH-2,
                height=INST_HEIGHT-2,
                callback=on_instance_click,
                user_data={"index":i}
            )
            with dpg.tooltip(dpg.last_item()):
                dpg.add_text(instance["name"])
                dpg.add_text(f"Version: {instance['version']}\nLoader: {instance['loader']}")
            col = (col+1)%cols
            if col == 0:
                rows += 1
                instances_rows.append(dpg.add_table_row(tag=f"table_row_{rows}"))

def on_viewport_resize(sender,app_data):
    width,height = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
    dpg.set_item_pos("root_window",(0,0))
    dpg.set_item_width("root_window",width)
    dpg.set_item_width("left_pane",width-200)
    dpg.set_item_height("root_window",height)
    rebuildInstancesPane()
def on_window_close():
    dpg.stop_dearpygui()
versions = version.get()
minecraftVersions = {x.id:x for x in versions}
def launchGame(si):
    global shared_assets_progress
    thisVer = minecraftVersions[si["version"]]
    loaderId = si["loader"].lower()
    versionId = thisVer.id + f"-{loaderId}"
    versionType = thisVer.type
    try:
        shared_assets_progress = "Downloading: JSON"
        modloader = version.Modloaders.UNKNOWN
        for i in version.Modloaders:
            if i.name.lower() == loaderId:
                modloader = i
        if modloader == version.Modloaders.UNKNOWN:
            d.err("Modloader type could not be determined!")
            raise IllegalStateError("No modloader type!")
        json = version.download(f"versions/{versionId}/",version=thisVer,type="json",modloader=modloader,modloaderVersion={"loader":"0.18.4"})
        assets = { # this is all the info i need.
            "id":json["assetIndex"]["id"],
            "sha1":json["assetIndex"]["sha1"]
        }
        javaVersion = str(json["javaVersion"]["majorVersion"])
        if not javaVersion in javas:
            shared_assets_progress = f"Downloading: Java {javaVersion}"
            d.info(f"Couldn't find java version {javaVersion}; installing it.")
            d.debug(f"Java versions: {javas}")
            backend.java.getJava(javaVersion)
            loadJavas()
        shared_assets_progress = "Downloading: Asset Index"
        version.download(f"assets/indexes/",json=json,type="assetIndex",sha1=assets["sha1"])
        shared_assets_progress = "Downloading: Assets (this may take up to 10 minutes)"
        _assets.download(f"assets/objects",f"assets/indexes/{assets['id']}.json")
        shared_assets_progress = "Downloading: Minecraft Client"
        version.download(f"versions/{versionId}/",json=json,type="jar",modloader=modloader,modloaderVersion={"loader":"0.18.4"})
        shared_assets_progress = "Downloading: System Libraries"
        version.download(f"versions/{versionId}/natives",json=json,type="natives")
        shared_assets_progress = "Downloading: Java Libraries"
        version.download(f"versions/{versionId}/libraries",json=json,type="libraries")
        shared_assets_progress = "Downloading: Mod Files"
        rebuildMods(si)
        shared_assets_progress = None
        javaPath = javas[javaVersion]
        run = backend.java.Runner(javaPath,f"versions/{versionId}/natives",backend.java.Memory(512,2048),backend.brand.Brand("Quartz","1.0.0"),
                backend.java.ClassPath(f"versions/{versionId}/libraries",f"versions/{versionId}/client.jar"),backend.java.Instance(versionId,versionType,
                f"{si["path"]}",backend.java.Assets("assets/",f"{assets['id']}"),json["mainClass"]),backend.auth.offline("quartz_dev"),
                backend.java.ExtraArgs("",""))
        run.run()
    except Exception as e:
        fatalError(e)
def on_si_play():
    loadInstances()
    si = instances[selectedInstance]
    threading.Thread(target=launchGame,daemon=True,args=[si]).start()
def on_si_edit(a,b,inst=None):
    if inst == None:
        global editedInstance
        inst = selectedInstance
    editedInstance = inst
    print(inst,selectedInstance,editedInstance)
    # dpg.configure_item("edit_instancename",enabled=(inst!=-1))
    # dpg.configure_item("edit_instanceversion",enabled=(inst!=-1))
    dpg.configure_item("edit_instance_general",show=(inst!=-1))
    dpg.set_value("edit_instancename",getInstance(editedInstance)["name"])
    dpg.set_value("edit_instanceversion",getInstance(editedInstance)["version"])
    dpg.set_value("edit_instanceloader",getInstance(editedInstance)["loader"])
    rebuildModsList()
    showCentered("edit_instance")

def on_si_editRoot(a,b,_):
    return on_si_edit(a,b,-1)

def edit_on_close():
    print("buh")
    if not dpg.get_value("edit_instancesaved"):
        dpg.show_item("edit_instance")
        dpg.set_item_label("edit_instance","*** Unsaved changes! ***")
        end_frame = dpg.get_frame_count()+60
        def callback():
            dpg.set_item_label("edit_instance","editing an instance")
        dpg.set_frame_callback(end_frame,callback)
    else:
        si_edit_cancel()
def si_edit_save():
    ei = getInstance(editedInstance)

    if not dpg.get_value("edit_instanceloader") and editedInstance != -1:
        def callback():
            dpg.set_item_label("edit_instanceloader","Mod Loader")
        dpg.set_item_label("edit_instanceloader","Mod Loader (required)")
        end_frame = dpg.get_frame_count()+60
        dpg.set_frame_callback(end_frame,callback=callback)
        return

    ei["name"] = dpg.get_value("edit_instancename")
    ei["version"] = dpg.get_value("edit_instanceversion")
    ei["loader"] = dpg.get_value("edit_instanceloader")

    if ei["path"] == None:
        ei["path"] = "instances/" + "".join([x.replace(" ","-").lower() for x in ei["name"] if x.isalnum() or x in "- "])

    dpg.set_value("edit_instancesaved",True)
    saveInstance(ei)
    loadInstances()
    rebuildInstancesPane()
def si_edit_cancel():
    dpg.set_value("edit_instancesaved",True)
    dpg.hide_item("edit_instance")
    loadInstances()
    rebuildInstancesPane()
def si_edit_deletemod(a,b,mod):
    idx = mod[0]
    modObj = mod[1]
    ei = getInstance(editedInstance)
    ei["mods"].pop(idx)
    rebuildModsList()
    dpg.set_value("edit_instancesaved",False)
    on_si_sync()
def si_edit_modenabled(a,b,mod):
    idx = mod[0]
    modObj = mod[1]
    modObj.enabled = not modObj.enabled
    dpg.set_value("edit_instancesaved",False)
def ei_add_mod(a,b,c):
    global modsearch_mode
    modsearch_mode = "add"
    showCentered("ei_mod_search")
    ei_make_search(0,0,0)
def ei_make_search(a,b,c):
    ei = getInstance(editedInstance)
    if ei["loader"] == "Vanilla":
        raise IllegalStateError("Searching for mods for a vanilla instance is not allowed.")
    query = dpg.get_value("ei_mod_searchbar")
    facets = []
    if ei["version"] != "":
        facets += [
            [f"versions:{ei['version']}"]
        ]
    if ei["loader"] != "":
        loaderCat = mods.LOADER_MAP[ei["loader"].lower()]
        facets += [
            [f"categories:{loaderCat}"]
        ]
    params = {
        "query":query
        }
    if facets != []:
        params["facets"] = js.dumps(facets)
    print(params)
    r = requests.get("https://api.modrinth.com/v2/search",params)
    searchResults = r.json()
    if r.status_code != 200:
        d.err(searchResults)
        raise Exception()
    d.debug(searchResults)
    versions = [x["latest_version"] for x in searchResults["hits"]]
    params = {
        "ids":js.dumps(versions)
    }
    r = requests.get("https://api.modrinth.com/v2/versions",params)
    versionResults = r.json()
    if r.status_code != 200:
        d.err(searchResults)
        raise Exception()
    versionIdNames = {}
    for i,obj in enumerate(versionResults):
        versionIdNames[obj["id"]] = obj["version_number"]
    modList = [mods.Mod(x["slug"],x["latest_version"],x["title"],versionIdNames[x["latest_version"]],x["description"],ei["version"],ei["loader"],False,True,fillNull=False) for x in searchResults["hits"]]
    rebuildSearchResults(modList)
def si_installMod(a,b,mod):
    ei = getInstance(editedInstance)
    ei["mods"].append(mods.Mod(*mod))
    rebuildModsList()
    dpg.set_value("edit_instancesaved",False)
def si_edit_modrootignore(a,b,mod):
    idx = mod[0]
    modObj = mod[1]
    inst = editedInstance
    rskip = instances[inst]["rootSkipped"]
    if modObj.id in rskip:
        rskip.remove(modObj.id)
    else:
        rskip.append(modObj.id)
    dpg.set_value("edit_instancesaved",False)
def on_si_sync():
    si = instances[selectedInstance]
    modsFolder = os.path.join(si["path"],"mods")
    if modsFolder:
        shutil.rmtree(modsFolder)
def on_si_newInstance():
    global instances,selectedInstance
    instances += [{
        "format":version.QUARTZ_JSON_LATEST,
        "path":None,
        "name":"Untitled",
        "version":list(minecraftVersions.keys())[0],
        "loader":"",
        "mods":[],
        "rootSkipped":[]
    }]
    selectedInstance = len(instances)-1
    on_si_edit(0,0)

shared_assets_progress = None
def before_render():
    if shared_assets_progress is not None:
        dpg.set_value("assets_progress",shared_assets_progress)
        dpg.show_item("play_assets")
    else:
        dpg.hide_item("play_assets")
    if len(instances) == 0:
        dpg.set_value("si_name","No instance selected.")
        dpg.set_value("si_ver","")
        dpg.set_value("si_loader","")
    else:
        dpg.set_value("si_name",instances[selectedInstance]["name"])
        dpg.set_value("si_ver","Version: " + instances[selectedInstance]["version"])
        dpg.set_value("si_loader","Loader: " + instances[selectedInstance]["loader"])

dpg.create_context()
dpg.create_viewport()
dpg.set_viewport_resize_callback(on_viewport_resize)
dpg.setup_dearpygui()

themes.create()

dpg.bind_theme("quartz_theme")

def loadJavas():
    global javas
    os.makedirs("java",exist_ok=True)
    os.makedirs("instances",exist_ok=True)
    if not "quartzroot.json" in os.listdir("instances"):
        with open("instances/quartzroot.json","w") as f:
            f.write("""{
    "format": 2,
    "mods": [],
    "version": "",
    "loader": "",
    "path": "instances/quartzroot.json",
    "name": "unused"
}""")
    javas = os.listdir("java")
    javas = {x:os.path.join("java",x,"bin/java") for x in javas}

loadJavas()

def loadQuartzInstance(jsonPath,path=None):
    with open(jsonPath,"r") as f:
        jsonFile = js.load(f)
    jsonFile["path"] = path or jsonPath
    print(jsonFile)
    version.upgradeQuartz(jsonFile)
    jsonFile["mods"] = [mods.Mod(*x) for x in jsonFile["mods"]]
    return jsonFile

def saveInstance(inst):
    inst["mods"] = [x.serialize() for x in inst["mods"]]
    path = inst["path"]
    if path.endswith(".json"):
        os.makedirs(os.path.dirname(path),exist_ok=True)
        jsonPath = path
    else:
        os.makedirs(path,exist_ok=True)
        jsonPath = os.path.join(path,"quartz.json")
    with open(jsonPath,"w") as f:
        js.dump(inst,f)

def loadInstances():
    global instances,root

    instances = []
    for name in os.listdir("instances"):
        path = os.path.join("instances/",name)
        if pathlib.Path(path).is_dir():
            jsonPath = os.path.join(path,"quartz.json")
            instances.append(loadQuartzInstance(jsonPath,path))
    root = loadQuartzInstance("instances/quartzroot.json")
    root["name"] = "root"
    root["name"] = "unused"

def getInstance(idx):
    if idx == -1:
        return root
    else:
        print(instances,idx)
        return instances[idx]

loadInstances()

# instances = [
#     {
#         "path":"instances/demo",
#         "name":"This is an instance",
#         "version":"1.21.11",
#         "loader":"Fabric",
#         "mods":[
#         ],
#         "rootSkipped":[
#         ]
#     },
#     {
#         "path":"instances/demo2",
#         "name":"Another",
#         "version":"1.21.5",
#         "loader":"Fabric",
#         "mods":[
#         ],
#         "rootSkipped":[
#         ]
#     },
# ]

# root = {
#     "mods":[
#         mods.Mod("fabric-api","DdVHbeR1"),
#         mods.Mod("modmenu","hGuj7hNc"),
#         mods.Mod("appleskin","pvcLnrm0")
#     ]
# }

selectedInstance = 0

def showCentered(tag):
    itemPos = [dpg.get_item_width(tag)/2,dpg.get_item_height(tag)/2]
    pos = [dpg.get_viewport_width()/2,dpg.get_viewport_height()/2]
    pos = [x-(itemPos[i]) for i,x in enumerate(pos)]
    dpg.set_item_pos(tag,pos)
    dpg.show_item(tag)

def rebuildModsList():
    d.debug("Rebuilding mods list...")
    if dpg.does_item_exist("ei_mods_list"):
        dpg.delete_item("ei_mods_list")
    with dpg.table(tag="ei_mods_list",parent="ei_mods",row_background=True,policy=dpg.mvTable_SizingFixedFit):
        if editedInstance != -1: dpg.add_table_column(label="Enable")
        dpg.add_table_column(label="Mod Id")
        dpg.add_table_column(label="Version")
        dpg.add_table_column(label="Actions",width=100)
        thisInstance = getInstance(editedInstance)
        thisInstanceMods = thisInstance["mods"]
        d.debug(editedInstance)
        if editedInstance != -1:
            rootMods = getInstance(-1)["mods"]
        else:
            rootMods = []
        def addRow(idx,mod,root=False):
            d.debug(mod.serialize())
            with dpg.table_row() as row:
                if root: dpg.bind_item_theme(row,"quartz_inherited_row")
                if editedInstance != -1:
                    with dpg.table_cell():
                        callback = si_edit_modenabled
                        value = mod.enabled
                        if root:
                            value = not mod.id in thisInstance["rootSkipped"]
                            callback = si_edit_modrootignore
                        dpg.add_checkbox(default_value=value,user_data=(idx,mod),callback=callback)
                with dpg.table_cell():
                    dpg.add_text(mod.displayName)
                with dpg.table_cell():
                    with dpg.child_window(width=100,height=20,border=False,horizontal_scrollbar=False,menubar=False):
                        dpg.bind_item_theme(dpg.last_item(),"invisible_child")
                        dpg.add_text(mod.displayVersion)
                with dpg.table_cell():
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Delete",user_data=(idx,mod),callback=si_edit_deletemod,enabled=(not root))
                        if root:
                            with dpg.tooltip(parent=dpg.last_item()):
                                dpg.add_text("Deleting mods is disabled, because this is a root mod.\nUse the enabled field instead.\n\nIf you would like to delete this from the root instance, you must do it from the root instance.",wrap=200)
                        dpg.add_button(label="Update")
        for i,mod in enumerate(rootMods):
            addRow(i,mod,True)
        for i,mod in enumerate(thisInstanceMods):
            addRow(i,mod)

d.warn("Testing mods are in the demo instance. Remember to get rid of them!")
with dpg.window(tag="play_assets",label="preparing to launch...",show=False):
    dpg.add_text("Preparing to launch Minecraft...")
    dpg.add_text("Downloading: JSON",tag="assets_progress")
with dpg.window(tag="root_window",label="quartz",width=600,height=400,no_resize=True,no_move=True,no_collapse=True,on_close=on_window_close,
                no_bring_to_front_on_focus=True):
    with dpg.menu_bar():
        dpg.add_button(label="Create Instance",callback=on_si_newInstance)
        dpg.add_button(label="Open Root Instance",callback=on_si_editRoot)
        with dpg.menu(label="Settings"):
            dpg.add_button(label="Settings")
            dpg.add_button(label="About")
            dpg.add_button(label="Restart Guide")
    with dpg.group(horizontal=True):
        with dpg.child_window(tag="left_pane"):
            # dpg.add_text(default_value="left pane")
            pass
        with dpg.child_window(tag="right_pane",border=True):
            dpg.add_text(default_value="Options for instance:")
            dpg.add_text(tag="si_name",default_value="A particularly long instance name",wrap=180)

            dpg.add_spacer(height=10)

            dpg.add_text(tag="si_ver",default_value="Version: 1.21.11",wrap=180)
            dpg.add_text(tag="si_loader",default_value="Loader: Fabric",wrap=180)

            dpg.add_spacer(height=20)

            dpg.add_button(label="Play",callback=on_si_play)

            dpg.add_spacer(height=20)

            dpg.add_button(label="Edit",callback=on_si_edit)
            dpg.add_button(label="Rename")
            dpg.add_button(label="Update Mods")
            dpg.add_button(label="Sync Mods",callback=on_si_sync)
            with dpg.tooltip(parent=dpg.last_item()):
                dpg.add_text("Completes any changes made.\n\nThis is needed because skipping root mods does NOT automatically remove those mods.\n\nInternally, this deletes all of your mods (ONLY the .JARs), and reinstalls them next time you launch the game.",wrap=200)

            dpg.add_spacer(height=20)

            dpg.add_button(label="Delete")
editedInstance = 0
with dpg.window(tag="edit_instance",label="editing an instance",show=False,no_collapse=True,no_close=False,on_close=edit_on_close,autosize=True,min_size=(200,50)):
    with dpg.tab_bar():
        with dpg.tab(tag="edit_instance_general",label="General"):
            d.warn("Edit Instance window is shown by default.")
            dpg.add_input_text(tag="edit_instancename",label="Instance Name",default_value="")
            dpg.add_combo(tag="edit_instanceversion",items=list(minecraftVersions.keys()),default_value="1.21.11",label="Minecraft Version",height_mode=dpg.mvComboHeight_Large)
            dpg.add_combo(tag="edit_instanceloader",items=["Vanilla","Fabric","LexForge","NeoForge","Quilt","Babric","BTA","Java Agent","Legacy Fabric","LiteLoader","Risugami's ModLoader","NilLoader","Ornithe","Rift"],default_value="Vanilla",label="Mod Loader",height_mode=dpg.mvComboHeight_Large)
            dpg.add_checkbox(tag="edit_instancesaved",default_value=False,show=False)
        with dpg.tab(tag="ei_mods",label="Mods"):
            with dpg.group(horizontal=True):
                dpg.add_button(tag="ei_add_mod",label="Add Mod",callback=ei_add_mod)
                dpg.add_button(tag="ei_update_all",label="Update All")

    with dpg.group(horizontal=True):
        dpg.add_button(label="Save",callback=si_edit_save)
        dpg.add_button(label="Cancel",callback=si_edit_cancel)
with dpg.window(tag="ei_mod_search",label="Adding mods",autosize=True,show=False):
    with dpg.group(horizontal=True,horizontal_spacing=10):
        dpg.add_input_text(tag="ei_mod_searchbar",width=215)
        dpg.add_button(label="Search",callback=ei_make_search,width=75)
    with dpg.child_window(tag="ei_mod_search_results",height=300,width=300):
        pass
dpg.show_viewport()
def initFrame():
    rebuildInstancesPane()
    # on_si_edit(None,None,selectedInstance)
dpg.set_frame_callback(2,initFrame)
if not dpg.is_viewport_ok():
    raise RuntimeError("DearPyGUI fail.")
while dpg.is_dearpygui_running():
    before_render()
    dpg.render_dearpygui_frame()
dpg.destroy_context()