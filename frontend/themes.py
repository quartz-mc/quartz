import dearpygui.dearpygui as dpg
def create():
    with dpg.theme(tag="quartz_theme"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive,(180,180,180,255))
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg,(220,220,220,255))
            dpg.add_theme_color(dpg.mvThemeCol_Button,(200,200,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_Button,(200,200,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,(180,180,180,255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,(160,160,160,255))
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg,(240,240,240,255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg,(240,240,240,255))
            dpg.add_theme_color(dpg.mvThemeCol_Border,(200,200,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_Text,(30,30,30,255))
            dpg.add_theme_color(dpg.mvThemeCol_Header,(200,200,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered,(180,180,180,255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive,(160,160,160,255))