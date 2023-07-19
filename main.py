import PySimpleGUI as sg
from clenv.cli.config.config_manager import ConfigManager
import webbrowser as wb
import json

from utils import *

################################################################################
######                          Initialization                            ######
################################################################################

# make a custom theme using colors from the actual clearML website
sg.LOOK_AND_FEEL_TABLE['clearML'] = {
    'BACKGROUND': '#1A1E2C',
    'TEXT': '#ffffff',
    'INPUT': '#384161',
    'TEXT_INPUT': '#ffffff',
    'SCROLL': '#ffffff',
    'BUTTON': ('#ffffff', '#384161'),
    'PROGRESS': ('#ffffff', '#384161'),
    'BORDER': 1, 'SLIDER_DEPTH': 0, 
    'PROGRESS_DEPTH': 0,
}
sg.theme('clearML')

# import layouts from layouts.py
from layouts import (
    main_layout, 
    run_template_layout, 
    exec_layout, 
    exec_complete_layout, 
    config_layout, 
    config_checkout_layout, 
    config_create_layout, 
    config_delete_layout, 
    config_list_layout, 
    config_rename_layout, 
    config_configure_layout
)

# Main layout
layout = [
    [sg.Text('')],
    [sg.Image('./logo.png')],
    [sg.Text('')],
    [sg.Column(main_layout, key='main_layout'),
     sg.Column(exec_layout, visible=False, key='exec_layout'), 
     sg.Column(exec_complete_layout, visible=False, key='exec_complete_layout'),
     sg.Column(config_layout, visible=False, key='config_layout'),
     sg.Column(config_checkout_layout, visible=False, key='config_checkout_layout'),
     sg.Column(config_create_layout, visible=False, key='config_create_layout'),
     sg.Column(config_delete_layout, visible=False, key='config_delete_layout'),
     sg.Column(config_list_layout, visible=False, key='config_list_layout'),
     sg.Column(config_rename_layout, visible=False, key='config_rename_layout'),
     sg.Column(config_configure_layout, visible=False, key='config_configure_layout'),
     sg.Column(run_template_layout, visible=False, key='run_template_layout')]
]

main_window = ActiveWindow(sg.Window('CLENV', layout, modal=True, size=(700, 700), element_justification='c'), active=True)

# init the app, which takes windows, config_manager, URL, and run_config params
app = App({main_window.name:main_window}, ConfigManager('~/.clenv-config-index.json'), '', {})

################################################################################
######                        Window Controllers                          ######
################################################################################

def main(main_event, main_values):
    if main_event == sg.WIN_CLOSED: # if user closes window or clicks cancel
        return False
    
    # main menu controllers
    if main_event == 'task_exec':
        app.task_exec()
    if main_event == 'config':
        app.config()
    
    # config controllers
    if main_event == 'config_confirm':
        app.config_confirm(main_values)
    if main_event == 'config_back':
        app.config_back()
    for option_back in ['config_checkout_back',
                        'config_create_back', 
                        'config_delete_back', 
                        'config_list_back', 
                        'config_rename_back', 
                        'config_configure_back']:
        if main_event == option_back:
            app.option_back(option_back)
    if main_event == 'config_checkout_confirm':
        app.config_checkout_confirm(main_values)
    if main_event == 'config_create_confirm':
        app.config_create_confirm(main_values)
    if main_event == 'config_delete_confirm':
        app.config_delete_confirm(main_values)
    if main_event == 'config_rename_confirm':
        app.config_rename_confirm(main_values)
    if main_event == 'config_configure_confirm':
        app.config_configure_confirm(main_values)
        
    # run template controllers
    if main_event == 'run_template_new':
        app.run_template_new()
    if main_event == 'run_template_template':
        app.run_template_template(main_values)
    if main_event == 'run_template_delete':
        app.run_template_delete(main_values)
    if main_event == 'run_template_back':
        app.run_template_back()

    # exec controllers
    if main_event == 'exec_back':
        app.exec_back()
    if main_event == 'exec_confirm':
        app.exec_confirm(main_values)
    if main_event == 'exec_complete_URL':
        wb.open(app.URL)
    if main_event == 'exec_complete_back':
        app.exec_complete_back()
    return True

def new_config(new_config_event, new_config_values):
    if new_config_event == 'Confirm' or new_config_event == sg.WIN_CLOSED:
        if new_config_event == 'Confirm':
            app.config_manager.initialize_profile(f'{new_config_values[0]}')
            app.main_window.window['main_layout'].update(visible=False)
            app.main_window.window['config_layout'].update(visible=True)
        app.windows['Profile Configuration'].window.close()
        app.windows.pop('Profile Configuration')
        app.main_window.set_active()

def new_template(new_template_event, new_template_values):
    if new_template_event == 'Confirm' or new_template_event == sg.WIN_CLOSED:
        if new_template_event == 'Confirm':
            template_name = new_template_values[0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            current_templates[template_name] = app.run_config
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            app.main_window.window['template_chosen'].update(values=template_names)
            task = exec_config(app.run_config, app.main_window.window)
            app.url = task.get_output_log_web_page()
        app.windows['Template Creation'].window.close()
        app.windows.pop('Template Creation')
        app.main_window.set_active()

def error(error_event, error_values):
    if error_event == 'Back' or error_event == sg.WIN_CLOSED:
        app.windows['Error'].window.close()
        app.windows.pop('Error')
        app.main_window.set_active()

def action_successful(action_successful_event, action_successful_values):
    if action_successful_event == sg.WIN_CLOSED:
        app.windows['Action Successful'].window.close()
        app.windows.pop('Action Successful')
        app.main_window.set_active()

################################################################################
######                             Main Loop                              ######
################################################################################

while True:
    window = app.get_active_window()
    event, values = window.window.read()
    if window.name == 'CLENV':
        # only way to exit the main loop is by closing the main window
        if not main(event, values):
            break
    elif window.name == 'Profile Configuration':
        new_config(event, values)
    elif window.name == 'Template Creation':
        new_template(event, values)
    elif window.name == 'Error':
        error(event, values)
    elif window.name == 'Action Successful':
        action_successful(event, values)

# closes all windows
for name in app.windows:
    app.windows[name].window.close()