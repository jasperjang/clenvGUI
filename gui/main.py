import PySimpleGUI as sg
from git import Repo
from os.path import isfile
from clenv.cli.config.config_manager import ConfigManager
import webbrowser as wb
import os, json

from utils import *

################################################################################
######                          Initialization                            ######
################################################################################

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

config_manager = ConfigManager('~/.clenv-config-index.json')

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

windows = {main_window.name:main_window}

URL = ''
run_config = {}

################################################################################
######                        Window Controllers                          ######
################################################################################

def main(main_event, main_values):
    global windows
    if main_event == sg.WIN_CLOSED: # if user closes window or clicks cancel
        return False
    
    # main menu controllers
    if main_event == 'task_exec':
        if not isfile('./task_templates.json'):
            with open('task_templates.json', 'w') as f:
                json.dump({}, f, indent=4)
        with open("task_templates.json", "r") as f:
            current_templates = json.load(f)
        template_names = get_template_names(current_templates)
        main_window.window['template_chosen'].update(values=template_names)
        main_window.window['main_layout'].update(visible=False)
        main_window.window['run_template_layout'].update(visible=True)
    if main_event == 'config':
        if not config_manager.profile_has_initialized():
            new_config_layout = [
                [sg.Text('Please input a profile name:')],
                [sg.InputText()],
                [sg.Button('Confirm')]
            ]
            new_config_window = ActiveWindow(sg.Window('Profile Creation', new_config_layout, modal=True), active=True)
            windows[new_config_window.name] = new_config_window
            windows['CLENV'].set_inactive()
            
        else:
            main_window.window['main_layout'].update(visible=False)
            main_window.window['config_layout'].update(visible=True)
    
    # config controllers
    if main_event == 'config_confirm':
        option = main_values['config_options']
        if option == '':
            return True
        # option_layout is the string key associated with the layout of the option selected in the dropdown menu
        option_layout = f'config_{option.split(" ")[0].lower()}_layout'
        active_profile = config_manager.get_active_profile()[0]
        non_active_profiles = config_manager.get_non_active_profiles()
        non_active_profile_names = get_non_active_profile_names(non_active_profiles)
        profile_list = get_profile_list(active_profile, non_active_profiles)
        # reset layout whenever selected
        if option_layout == 'config_checkout_layout':
            main_window.window['checkout_active_profile'].update(f'Active Profile: {active_profile["profile_name"]}')
            main_window.window['checkout_non_active_profiles'].update(values=non_active_profile_names)
        elif option_layout == 'config_create_layout':
            main_window.window['new_profile_name'].update('')
        elif option_layout == 'config_delete_layout':
            main_window.window['delete_non_active_profiles'].update(values=non_active_profile_names)
            main_window.window['delete_non_active_profiles'].update('')
        elif option_layout == 'config_list_layout':
            profile_string = get_profile_string(get_profile_list(active_profile, non_active_profiles))
            main_window.window['profile_list'].update(profile_string)
        elif option_layout == 'config_rename_layout':
            main_window.window['profile_list_menu'].update(values=profile_list)
            main_window.window['profile_rename'].update('')
        elif option_layout == 'config_configure_layout':
            main_window.window['profile_to_config'].update(values=profile_list)
            main_window.window['profile_to_config'].update('')
            main_window.window['multiline_config'].update('')
        
        main_window.window['config_layout'].update(visible=False)
        main_window.window[option_layout].update(visible=True)
    if main_event == 'config_back':
        main_window.window['config_options'].update('')
        main_window.window['config_layout'].update(visible=False)
        main_window.window['main_layout'].update(visible=True)
    for option_back in ['config_checkout_back',
                        'config_create_back', 
                        'config_delete_back', 
                        'config_list_back', 
                        'config_rename_back', 
                        'config_configure_back']:
        if main_event == option_back:
            main_window.window[f'{option_back.split("back")[0]}layout'].update(visible=False)
            main_window.window['config_options'].update('')
            main_window.window['config_layout'].update(visible=True)
    if main_event == 'config_checkout_confirm':
        profileName = main_values['checkout_non_active_profiles']
        if config_manager.has_profile(profile_name=profileName):
            config_manager.set_active_profile(profileName)
            windows = action_success(main_window.window, windows)
            main_window.window['config_checkout_layout'].update(visible=False)
            main_window.window['config_layout'].update(visible=True)
    if main_event == 'config_create_confirm':
        new_profile_name = main_values['new_profile_name']
        if config_manager.has_profile(profile_name=new_profile_name):
            windows = create_error_window('profile already exists', windows)
        else:
            config_manager.create_profile(new_profile_name)
            windows = action_success(main_window.window, windows)
            main_window.window['config_create_layout'].update(visible=False)
            main_window.window['config_layout'].update(visible=True)
    if main_event == 'config_delete_confirm':
        profile_to_delete = main_values['delete_non_active_profiles']
        config_manager.delete_profile(profile_to_delete)
        windows = action_success(main_window.window, windows)
        main_window.window['config_delete_layout'].update(visible=False)
        main_window.window['config_layout'].update(visible=True)
    if main_event == 'config_rename_confirm':
        profile_to_rename = main_values['profile_list_menu']
        profile_rename = main_values['profile_rename']
        if profile_rename in profile_list:
            windows = create_error_window('profile name is already taken', windows)
        elif profile_to_rename == '' or profile_rename == '':
            windows,  = create_error_window('one or more options is blank', windows)
        else:
            config_manager.rename_profile(profile_to_rename, profile_rename)
            windows = action_success(main_window.window, windows)
            main_window.window['config_rename_layout'].update(visible=False)
            main_window.window['config_layout'].update(visible=True)
    if main_event == 'config_configure_confirm':
        profile_to_config = main_values['profile_to_config']
        config = main_values['multiline_config']
        try:
            config_manager.reinitialize_api_config(profile_to_config, config)
            windows = action_success(main_window.window, windows)
            main_window.window['config_configure_layout'].update(visible=False)
            main_window.window['config_layout'].update(visible=True)
        except:
            windows,  = create_error_window('invalid configuration format', windows)
    # run template controllers
    if main_event == 'run_template_new':
        queue_list = get_queue_list()
        main_window.window['queue_list'].update(values=queue_list)
        main_window.window['save_as_template'].update(False)
        main_window.window['run_template_layout'].update(visible=False)
        main_window.window['exec_layout'].update(visible=True)
    if main_event == 'run_template_template':
        if main_values['template_chosen'] != {} and main_values['template_chosen'] != []:
            queue_list = get_queue_list()
            main_window.window['queue_list'].update(values=queue_list)
            template_name = main_values['template_chosen'][0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            template = current_templates[template_name]
            queue_list = get_queue_list()
            queue = get_queue_from_name(template['queue'], queue_list)
            main_window.window['queue_list'].update(queue)
            main_window.window['task_types'].update(f'{template["task_type"]}')
            main_window.window['task_name'].update(f'{template["task_name"]}')
            main_window.window['path'].update(f'{template["path"]}')
            main_window.window['save_as_template'].update(False)
            main_window.window['run_template_layout'].update(visible=False)
            main_window.window['exec_layout'].update(visible=True)
        else:
            windows = create_error_window('no template selected', windows)
    if main_event == 'run_template_delete':
        if main_values['template_chosen'] != {} and main_values['template_chosen'] != []:
            template_name = main_values['template_chosen'][0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            current_templates.pop(template_name)
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            main_window.window['template_chosen'].update(values=template_names)
        else:
            windows = create_error_window('no template selected', windows)
    if main_event == 'run_template_back':
        main_window.window['run_template_layout'].update(visible=False)
        main_window.window['main_layout'].update(visible=True)
    # exec controllers
    if main_event == 'exec_back':
        main_window.window['exec_layout'].update(visible=False)
        main_window.window['run_template_layout'].update(visible=True)
        main_window.window['queue_list'].update('')
        main_window.window['task_types'].update('')
        main_window.window['task_name'].update('')
        main_window.window['path'].update('/')
    if main_event == 'exec_confirm':
        raw_queue_info = main_values['queue_list']
        task_type = main_values['task_types']
        task_name = main_values['task_name']
        path = main_values['path']
        raw_tags = main_values['tags']
        if check_blank_options(main_values):
            windows = create_error_window('one or more options is blank', windows)
        elif not isfile(path):
            windows = create_error_window('must input valid path', windows)
        else:
            queue, num_idle_workers, total_workers = get_queue_info(raw_queue_info)
            try:
                dir_path = os.path.dirname(path)
                repo = Repo(f'{dir_path}')
            except:
                windows = create_error_window('no git repository detected \nat specified file directory', windows)
            # Read the git information from current directory
            current_branch = repo.head.reference.name
            remote_url = repo.remotes.origin.url
            project_name = remote_url.split("/")[-1].split(".")[0]
            script = os.path.basename(path)
            tags = raw_tags.split(',')
            global run_config
            run_config = {
                    'project_name':project_name,
                    'task_name':task_name,
                    'task_type':task_type,
                    'repo':remote_url,
                    'branch':current_branch,
                    'path':path,
                    'script':script,
                    'queue':queue,
                    'tags':tags
                }
            if main_values['save_as_template']:  
                new_template_layout = [
                    [sg.Text('Please input a template name:')],
                    [sg.InputText()],
                    [sg.Button('Confirm')]
                ]
                new_template_window = ActiveWindow(sg.Window('Template Creation', new_template_layout, modal=True), active=True)
                windows[new_template_window.name] = new_template_window
                windows['CLENV'].set_inactive()
            else:
                task = exec_config(run_config, main_window.window)
                global URL
                URL = task.get_output_log_web_page()
    if main_event == 'exec_complete_URL':
        wb.open(URL)
    if main_event == 'exec_complete_back':
        main_window.window['queue_list'].update('')
        main_window.window['task_types'].update('')
        main_window.window['task_name'].update('')
        main_window.window['path'].update('/')
        main_window.window['save_as_template'].update(False)
        main_window.window['exec_complete_layout'].update(visible=False)
        main_window.window['run_template_layout'].update(visible=True)
    return True

def new_config(new_config_event, new_config_values):
    global windows
    if new_config_event == 'Confirm' or new_config_event == sg.WIN_CLOSED:
        if new_config_event == 'Confirm':
            config_manager.initialize_profile(f'{new_config_values[0]}')
            windows['CLENV'].window['main_layout'].update(visible=False)
            windows['CLENV'].window['config_layout'].update(visible=True)
        
        windows['Profile Configuration'].window.close()
        windows.pop('Profile Configuration')
        windows['CLENV'].set_active()

def new_template(new_template_event, new_template_values):
    global windows
    global run_config
    if new_template_event == 'Confirm' or new_template_event == sg.WIN_CLOSED:
        if new_template_event == 'Confirm':
            template_name = new_template_values[0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            current_templates[template_name] = run_config
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            windows['CLENV'].window['template_chosen'].update(values=template_names)
            task = exec_config(run_config, windows['CLENV'].window)
            URL = task.get_output_log_web_page()
        windows['Template Creation'].window.close()
        windows.pop('Template Creation')
        windows['CLENV'].set_active()

def error(error_event, error_values):
    global windows
    if error_event == 'Back' or error_event == sg.WIN_CLOSED:
        windows['Error'].window.close()
        windows.pop('Error')
        windows['CLENV'].set_active()

def action_successful(action_successful_event, action_successful_values):
    global windows
    if action_successful_event == sg.WIN_CLOSED:
        windows['Action Successful'].window.close()
        windows.pop('Action Successful')
        windows['CLENV'].set_active()

################################################################################
######                             Main Loop                              ######
################################################################################

while True:
    window = get_active_window(windows)
    event, values = window.window.read()
    if window.name == 'CLENV':
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

for name in windows:
    windows[name].window.close()