import PySimpleGUI as sg
from clenv.cli.config.config_manager import ConfigManager
import webbrowser as wb
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
sg.set_options(font=('Arial', 14))

# import layouts from layouts.py
from layouts import (
    main_layout, 
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
    [
        sg.Column(main_layout, visible=True, key='main_layout'),
        sg.Column(exec_layout, visible=False, key='exec_layout'), 
        sg.Column(exec_complete_layout, visible=False, key='exec_complete_layout'),
        sg.Column(config_layout, visible=False, key='config_layout'),
        sg.Column(config_checkout_layout, visible=False, key='config_checkout_layout'),
        sg.Column(config_create_layout, visible=False, key='config_create_layout'),
        sg.Column(config_delete_layout, visible=False, key='config_delete_layout'),
        sg.Column(config_list_layout, visible=False, key='config_list_layout'),
        sg.Column(config_rename_layout, visible=False, key='config_rename_layout'),
        sg.Column(config_configure_layout, visible=False, key='config_configure_layout')
    ]
]

window = sg.Window('CLENV', layout, modal=True, size=(700, 750), 
                   element_justification='c', finalize=True)

# init the app, which takes window, config_manager, URL, and run_config params
app = App(window, ConfigManager('~/.clenv-config-index.json'), '', {})
app.task_exec()

################################################################################
######                             Main Loop                              ######
################################################################################

while True:
    event, values = app.window.read()
    if event == 'quit' or event == sg.WIN_CLOSED: # if user closes window or clicks cancel
        break
    # main menu controllers
    if event == 'run_template_new':
        app.run_template_new()
    if event == 'run_template_template':
        app.run_template_template(values)
    if event == 'run_template_delete':
        app.run_template_delete(values)
    if event == 'config':
        app.config()
    
    # config controllers
    if event == 'config_confirm':
        app.config_confirm(values)
    if event == 'config_back':
        app.config_back()
    for option_back in ['config_checkout_back',
                        'config_create_back', 
                        'config_delete_back', 
                        'config_list_back', 
                        'config_rename_back', 
                        'config_configure_back']:
        if event == option_back:
            app.option_back(option_back)
    if event == 'config_checkout_confirm':
        app.config_checkout_confirm(values)
    if event == 'config_create_confirm':
        app.config_create_confirm(values)
    if event == 'config_delete_confirm':
        app.config_delete_confirm(values)
    if event == 'config_rename_confirm':
        app.config_rename_confirm(values)
    if event == 'config_configure_confirm':
        app.config_configure_confirm(values)

    # exec controllers
    if event == 'exec_back':
        app.exec_back()
    if event == 'exec_confirm':
        app.exec_confirm(values)
    if event == 'exec_complete_URL':
        wb.open(app.url)
    if event == 'exec_complete_back':
        app.exec_complete_back()

app.window.close()