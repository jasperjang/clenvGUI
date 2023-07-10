import PySimpleGUI as sg
from clearml import Task
from clearml.backend_interface.task.populate import CreateAndPopulate
from clenv.cli.queue.queue_manager import QueueManager
from git import Repo
from os.path import isfile
from clenv.cli.config.config_manager import ConfigManager
import webbrowser as wb
import os, json

from utils import (
    get_queue_list,
    get_queue_info,
    get_queue_from_name,
    check_blank_options,
    set_active_window,
    get_non_active_profile_names,
    get_profile_list,
    get_profile_string,
    action_success,
    create_error_window,
    get_template_names,
    exec_config
)

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

window_activity = {'main':True,
                  'error':False,
                  'new_config':False,
                  'action_successful':False,
                  'new_template':False}

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

main_window = sg.Window('CLENV', layout, modal=True, size=(700, 700), element_justification='c')

################################################################################
######                             Main Loop                              ######
################################################################################

while True:

    ######################### MAIN WINDOW CONTROLLERS ##########################
    if window_activity['main']:
        main_event, main_values = main_window.read()
        if main_event == sg.WIN_CLOSED: # if user closes window or clicks cancel
            break

        # main menu controllers
        if main_event == 'task_exec':
            if not isfile('./task_templates.json'):
                with open('task_templates.json', 'w') as f:
                    json.dump({}, f, indent=4)
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            template_names = get_template_names(current_templates)
            main_window['template_chosen'].update(values=template_names)
            main_window['main_layout'].update(visible=False)
            main_window['run_template_layout'].update(visible=True)
        if main_event == 'config':
            if not config_manager.profile_has_initialized():
                new_config_layout = [
                    [sg.Text('Please input a profile name:')],
                    [sg.InputText()],
                    [sg.Button('Confirm')]
                ]
                new_config_window = sg.Window('Profile Creation', new_config_layout, modal=True)
                window_activity = set_active_window('new_config', window_activity)
            else:
                main_window['main_layout'].update(visible=False)
                main_window['config_layout'].update(visible=True)
        
        # config controllers
        if main_event == 'config_confirm':
            option = main_values['config_options']
            if option == '':
                continue
            # option_layout is the string key associated with the layout of the option selected in the dropdown menu
            option_layout = f'config_{option.split(" ")[0].lower()}_layout'

            active_profile = config_manager.get_active_profile()[0]
            non_active_profiles = config_manager.get_non_active_profiles()
            non_active_profile_names = get_non_active_profile_names(non_active_profiles)
            profile_list = get_profile_list(active_profile, non_active_profiles)

            # reset layout whenever selected
            if option_layout == 'config_checkout_layout':
                main_window['checkout_active_profile'].update(f'Active Profile: {active_profile["profile_name"]}')
                main_window['checkout_non_active_profiles'].update(values=non_active_profile_names)
            elif option_layout == 'config_create_layout':
                main_window['new_profile_name'].update('')
            elif option_layout == 'config_delete_layout':
                main_window['delete_non_active_profiles'].update(values=non_active_profile_names)
                main_window['delete_non_active_profiles'].update('')
            elif option_layout == 'config_list_layout':
                profile_string = get_profile_string(get_profile_list(active_profile, non_active_profiles))
                main_window['profile_list'].update(profile_string)
            elif option_layout == 'config_rename_layout':
                main_window['profile_list_menu'].update(values=profile_list)
                main_window['profile_rename'].update('')
            elif option_layout == 'config_configure_layout':
                main_window['profile_to_config'].update(values=profile_list)
                main_window['profile_to_config'].update('')
                main_window['multiline_config'].update('')
            
            main_window['config_layout'].update(visible=False)
            main_window[option_layout].update(visible=True)
        if main_event == 'config_back':
            main_window['config_options'].update('')
            main_window['config_layout'].update(visible=False)
            main_window['main_layout'].update(visible=True)
        for option_back in ['config_checkout_back',
                            'config_create_back', 
                            'config_delete_back', 
                            'config_list_back', 
                            'config_rename_back', 
                            'config_configure_back']:
            if main_event == option_back:
                main_window[f'{option_back.split("back")[0]}layout'].update(visible=False)
                main_window['config_options'].update('')
                main_window['config_layout'].update(visible=True)
        if main_event == 'config_checkout_confirm':
            profileName = main_values['checkout_non_active_profiles']
            if config_manager.has_profile(profile_name=profileName):
                config_manager.set_active_profile(profileName)
                action_successful_window = action_success(main_window, window_activity)
                main_window['config_checkout_layout'].update(visible=False)
                main_window['config_layout'].update(visible=True)
        if main_event == 'config_create_confirm':
            new_profile_name = main_values['new_profile_name']
            if config_manager.has_profile(profile_name=new_profile_name):
                error_window, window_activity = create_error_window('profile already exists', window_activity)
            else:
                config_manager.create_profile(new_profile_name)
                action_successful_window = action_success(main_window, window_activity)
                main_window['config_create_layout'].update(visible=False)
                main_window['config_layout'].update(visible=True)
        if main_event == 'config_delete_confirm':
            profile_to_delete = main_values['delete_non_active_profiles']
            config_manager.delete_profile(profile_to_delete)
            action_successful_window = action_success(main_window, window_activity)
            main_window['config_delete_layout'].update(visible=False)
            main_window['config_layout'].update(visible=True)
        if main_event == 'config_rename_confirm':
            profile_to_rename = main_values['profile_list_menu']
            profile_rename = main_values['profile_rename']
            if profile_rename in profile_list:
                error_window, window_activity = create_error_window('profile name is already taken', window_activity)
            elif profile_to_rename == '' or profile_rename == '':
                error_window, window_activity = create_error_window('one or more options is blank', window_activity)
            else:
                config_manager.rename_profile(profile_to_rename, profile_rename)
                action_successful_window = action_success(main_window, window_activity)
                main_window['config_rename_layout'].update(visible=False)
                main_window['config_layout'].update(visible=True)
        if main_event == 'config_configure_confirm':
            profile_to_config = main_values['profile_to_config']
            config = main_values['multiline_config']
            try:
                config_manager.reinitialize_api_config(profile_to_config, config)
                action_successful_window = action_success(main_window, window_activity)
                main_window['config_configure_layout'].update(visible=False)
                main_window['config_layout'].update(visible=True)
            except:
                error_window, window_activity = create_error_window('invalid configuration format', window_activity)

        # run template controllers
        if main_event == 'run_template_new':
            queue_list = get_queue_list()
            main_window['queue_list'].update(values=queue_list)
            main_window['save_as_template'].update(False)
            main_window['run_template_layout'].update(visible=False)
            main_window['exec_layout'].update(visible=True)
        if main_event == 'run_template_template':
            if main_values['template_chosen'] != {} and main_values['template_chosen'] != []:
                queue_list = get_queue_list()
                main_window['queue_list'].update(values=queue_list)
                template_name = main_values['template_chosen'][0]
                with open("task_templates.json", "r") as f:
                    current_templates = json.load(f)
                template = current_templates[template_name]
                queue_list = get_queue_list()
                queue = get_queue_from_name(template['queue'], queue_list)
                main_window['queue_list'].update(queue)
                main_window['task_types'].update(f'{template["task_type"]}')
                main_window['task_name'].update(f'{template["task_name"]}')
                main_window['path'].update(f'{template["path"]}')
                main_window['save_as_template'].update(False)
                main_window['run_template_layout'].update(visible=False)
                main_window['exec_layout'].update(visible=True)
            else:
                error_window, window_activity = create_error_window('no template selected', window_activity)
        if main_event == 'run_template_delete':
            if main_values['template_chosen'] != {} and main_values['template_chosen'] != []:
                template_name = main_values['template_chosen'][0]
                with open("task_templates.json", "r") as f:
                    current_templates = json.load(f)
                current_templates.pop(template_name)
                with open("task_templates.json", "w") as f:
                    json.dump(current_templates, f, indent=4)
                template_names = get_template_names(current_templates)
                main_window['template_chosen'].update(values=template_names)
            else:
                error_window, window_activity = create_error_window('no template selected', window_activity)
        if main_event == 'run_template_back':
            main_window['run_template_layout'].update(visible=False)
            main_window['main_layout'].update(visible=True)

        # exec controllers
        if main_event == 'exec_back':
            main_window['exec_layout'].update(visible=False)
            main_window['run_template_layout'].update(visible=True)
            main_window['queue_list'].update('')
            main_window['task_types'].update('')
            main_window['task_name'].update('')
            main_window['path'].update('/')
        if main_event == 'exec_confirm':
            raw_queue_info = main_values['queue_list']
            task_type = main_values['task_types']
            task_name = main_values['task_name']
            path = main_values['path']
            raw_tags = main_values['tags']
            if check_blank_options(main_values):
                error_window, window_activity = create_error_window('one or more options is blank', window_activity)
            elif not isfile(path):
                error_window, window_activity = create_error_window('must input valid path', window_activity)
            else:
                queue, num_idle_workers, total_workers = get_queue_info(raw_queue_info)
                try:
                    dir_path = os.path.dirname(path)
                    repo = Repo(f'{dir_path}')
                except:
                    error_window, window_activity = create_error_window('no git repository detected \nat specified file directory', window_activity)
                # Read the git information from current directory
                current_branch = repo.head.reference.name
                remote_url = repo.remotes.origin.url
                project_name = remote_url.split("/")[-1].split(".")[0]
                script = os.path.basename(path)
                tags = raw_tags.split(',')
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
                    new_template_window = sg.Window('Template Creation', new_template_layout, modal=True)
                    window_activity = set_active_window('new_template', window_activity)
                else:
                    task = exec_config(run_config, main_window)
                    URL = task.get_output_log_web_page()
        if main_event == 'exec_complete_URL':
            wb.open(URL)
        if main_event == 'exec_complete_back':
            main_window['queue_list'].update('')
            main_window['task_types'].update('')
            main_window['task_name'].update('')
            main_window['path'].update('/')
            main_window['save_as_template'].update(False)
            main_window['exec_complete_layout'].update(visible=False)
            main_window['run_template_layout'].update(visible=True)
    
    ###################### NEW CONFIG WINDOW CONTROLLERS #######################
    if window_activity['new_config']:
        new_config_event, new_config_values = new_config_window.read()
        if new_config_event == 'Confirm':
            config_manager.initialize_profile(f'{new_config_values[0]}')
            active_profiles = config_manager.get_active_profile()
            non_active_profiles = config_manager.get_non_active_profiles()
            main_window['main_layout'].update(visible=False)
            main_window['config_layout'].update(visible=True)
            window_activity = set_active_window('main', window_activity)
            new_config_window.close()
        if new_config_event == sg.WIN_CLOSED:
            window_activity = set_active_window('main', window_activity)
            new_config_window.close()

    ##################### NEW TEMPLATE WINDOW CONTROLLERS ######################
    if window_activity['new_template']:
        new_template_event, new_template_values = new_template_window.read()
        if new_template_event == 'Confirm':
            template_name = new_template_values[0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            current_templates[template_name] = run_config
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            main_window['template_chosen'].update(values=template_names)
            window_activity = set_active_window('main', window_activity)
            new_template_window.close()
            task = exec_config(run_config, main_window)
            URL = task.get_output_log_web_page()
        if new_template_event == sg.WIN_CLOSED:
            window_activity = set_active_window('main', window_activity)
            new_template_window.close()

    ######################### ERROR WINDOW CONTROLLERS #########################
    if window_activity['error']:
        error_event, error_values = error_window.read()
        if error_event == 'Back' or error_event == sg.WIN_CLOSED:
            window_activity = set_active_window('main', window_activity)
            error_window.close()

    ################### ACTION SUCCESSFUL WINDOW CONTROLLERS ###################
    if window_activity['action_successful']:
        action_successful_event, action_successful_values = action_successful_window.read()
        if action_successful_event == sg.WIN_CLOSED:
            window_activity = set_active_window('main', window_activity)
            action_successful_window.close()

main_window.close()