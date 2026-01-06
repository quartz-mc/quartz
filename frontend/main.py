import dearpygui.dearpygui as dpg
import themes

def on_viewport_resize(sender,app_data):
    width,height = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
    dpg.set_item_pos("root_window",(0,0))
    dpg.set_item_width("root_window",width)
    dpg.set_item_width("left_pane",width-200)
    dpg.set_item_height("root_window",height)
def on_window_close():
    dpg.stop_dearpygui()

dpg.create_context()
dpg.create_viewport()
dpg.set_viewport_resize_callback(on_viewport_resize)
dpg.setup_dearpygui()

themes.create()

dpg.bind_theme("quartz_theme")

with dpg.window(tag="root_window",label="quartz",width=600,height=400,no_resize=True,no_move=True,no_collapse=True,on_close=on_window_close):
    with dpg.menu_bar():
        dpg.add_button(label="Create Instance")
        dpg.add_button(label="Open Root Instance",)
        with dpg.menu(label="Settings"):
            dpg.add_button(label="Settings")
            dpg.add_button(label="About")
            dpg.add_button(label="Restart Guide")
    with dpg.group(horizontal=True):
        with dpg.child_window(tag="left_pane"):
            dpg.add_text(default_value="left pane")
        with dpg.child_window(tag="right_pane",border=True):
            dpg.add_text(default_value="Instance")
            dpg.add_spacer(height=50)
            dpg.add_button(label="Play")
            dpg.add_spacer(height=20)
            dpg.add_button(label="Edit")
            dpg.add_button(label="Rename")
            dpg.add_button(label="Update Mods")
            dpg.add_spacer(height=20)
            dpg.add_button(label="Delete")

dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()