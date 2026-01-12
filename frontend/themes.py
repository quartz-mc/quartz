import dearpygui.dearpygui as dpg
def create():
    global mod_inherited_theme
    with dpg.theme(tag="quartz_theme"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg,(120,120,120,255))
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
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg,(240,240,240,255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,(200,200,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_Tab,(200,200,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive,(220,220,220,255))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered,(230,230,230,255))
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg,(200,200,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive,(220,220,220,255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered,(230,230,230,255))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg,(230,230,230,255))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt,(220,220,220,255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg,(220,220,220,255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab,(180,180,180,255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive,(200,200,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered,(190,190,190,255))
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize,5)
    with dpg.theme(tag="quartz_inherited_row"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg,(230,220,200,255))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt,(220,210,190,255))
    with dpg.theme(tag="invisible_child"):
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg,(240,240,240,0))