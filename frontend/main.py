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

def on_viewport_resize(sender,app_data):
    width,height = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
    dpg.set_item_pos("root_window",(0,0))
    dpg.set_item_width("root_window",width)
    dpg.set_item_width("left_pane",width-200)
    dpg.set_item_height("root_window",height)
def on_window_close():
    dpg.stop_dearpygui()
def on_si_play():
    with dpg.window():
        dpg.add_text("Downloading assets. This may take a tadbit.")
    si = instances[selectedInstance]
    versions = version.get()
    versionsDict = {x.id:x for x in versions}
    thisVer = versionsDict[si["version"]]
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
    javaPath = javas[0]
    run = backend.java.Runner(javaPath,f"versions/{versionId}/natives",backend.java.Memory(512,2048),backend.brand.Brand("Quartz","1.0.0"),
            backend.java.ClassPath("libraries/",f"versions/{versionId}/client.jar"),backend.java.Instance(versionId,versionType,"instances/demo",
            backend.java.Assets("assets/",f"{assets['id']}"),json["mainClass"]),backend.auth.offline("quartz_dev"),
            backend.java.ExtraArgs("",""))
    run.run()
def before_render():
    dpg.set_value("si_name",instances[selectedInstance]["name"])
    dpg.set_value("si_ver","Version: " + instances[selectedInstance]["version"])
    dpg.set_value("si_loader","Loader: " + instances[selectedInstance]["loader"])

dpg.create_context()
dpg.create_viewport()
dpg.set_viewport_resize_callback(on_viewport_resize)
dpg.setup_dearpygui()

themes.create()

dpg.bind_theme("quartz_theme")

javas = os.listdir("backend/java")

instances = [
    {
        "path":"backend/instances/demo",
        "name":"This is an instance",
        "version":"1.21.11",
        "loader":"Fabric",
        "nonRootMods":[
            mods.Mod("fabric-api","DdVHbeR1"),
            mods.Mod("modmenu","hGuj7hNc"),
            mods.Mod("appleskin","pvcLnrm0")
        ]
    }
]

selectedInstance = 0

d.warn("Testing mods are in the demo instance. Remember to get rid of them!")

with dpg.window(tag="root_window",label="quartz",width=600,height=400,no_resize=True,no_move=True,no_collapse=True,on_close=on_window_close):
    with dpg.menu_bar():
        dpg.add_button(label="Create Instance")
        dpg.add_button(label="Open Root Instance")
        with dpg.menu(label="Settings"):
            dpg.add_button(label="Settings")
            dpg.add_button(label="About")
            dpg.add_button(label="Restart Guide")
    with dpg.group(horizontal=True):
        with dpg.child_window(tag="left_pane"):
            dpg.add_text(default_value="left pane")
        with dpg.child_window(tag="right_pane",border=True):
            dpg.add_text(default_value="Options for instance:")
            dpg.add_text(tag="si_name",default_value="A particularly long instance name",wrap=180)
            dpg.add_spacer(height=10)
            dpg.add_text(tag="si_ver",default_value="Version: 1.21.11",wrap=180)
            dpg.add_text(tag="si_loader",default_value="Loader: Fabric",wrap=180)
            dpg.add_spacer(height=20)
            dpg.add_button(label="Play")
            dpg.add_spacer(height=20)
            dpg.add_button(label="Edit")
            dpg.add_button(label="Rename")
            dpg.add_button(label="Update Mods")
            dpg.add_spacer(height=20)
            dpg.add_button(label="Delete")

dpg.show_viewport()
if not dpg.is_viewport_ok():
    raise RuntimeError("DearPyGUI fail.")
while dpg.is_dearpygui_running():
    before_render()
    dpg.render_dearpygui_frame()
dpg.destroy_context()