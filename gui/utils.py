import PySimpleGUI as sg
from clearml import Task
from clearml.backend_interface.task.populate import CreateAndPopulate
from clenv.cli.queue.queue_manager import QueueManager
from git import Repo
from os.path import isfile
from clenv.cli.config.config_manager import ConfigManager
import webbrowser as wb
import os, json

################################################################################
######                         Helper Functions                           ######
################################################################################

# returns readable list of available queues
def get_queue_list():
    queue_manager = QueueManager()
    available_queues = queue_manager.get_available_queues()
    queue_list = []
    for queue in available_queues:
        queue_list.append(f"{queue['name']} - idle workers: {[worker['name'] for worker in queue['workers'] if worker['task'] is None]} - total workers: {len(queue['workers'])}")
    return queue_list

# returns queue name, number of idle workers, and total number of workers from the queue_list format above
def get_queue_info(queue_list_item):
    L = queue_list_item.split(' ')
    queue = L[0]
    num_idle_workers = len(L[4])
    total_workers = int(L[-1])
    return queue, num_idle_workers, total_workers

def get_queue_from_name(name, queue_list):
    for queue in queue_list:
        split_queue = queue.split(' ')
        if split_queue[0] == name:
            return queue

# checks if any values in the dictionary are empty
def check_blank_options(values):
    if (values['queue_list'] == '' or
        values['task_types'] == '' or
        values['task_name'] == '' or
        len(values['path']) <= 2):
        return True
    return False

# sets active window to the inputted window name
def set_active_window(window_name, window_activity):
    for window in window_activity:
        if window == window_name:
            window_activity[window] = True
        else:
            window_activity[window] = False
    return window_activity

# returns just the profile names from the list of non active profiles
def get_non_active_profile_names(non_active_profiles):
    non_active_profile_names = []
    for profile in non_active_profiles:
        non_active_profile_names.append(profile['profile_name'])
    return non_active_profile_names

# returns list of profile names
def get_profile_list(active_profile, non_active_profiles):
    profile_list = [active_profile['profile_name']]
    for profile in non_active_profiles:
        profile_list.append(profile["profile_name"])
    return profile_list

# returns string of profiles from the list of profile names
def get_profile_string(profile_list):
    profile_string = ''
    for profile_index in range(len(profile_list)):
        if profile_index == 0:
            profile_string += f'{profile_list[0]} <active>\n'
        else:
            profile_string += f'{profile_list[profile_index]}\n'
    return profile_string

# creates an action success window
def action_success(main_window, window_activity):
    main_window['config_options'].update('')
    action_successful_layout = [
        [sg.Text('Action completed successfully!')]
    ]
    action_successful_window = sg.Window('', action_successful_layout, modal=True)
    window_activity, set_active_window('action_successful', window_activity)
    return action_successful_window

# creates an error window
def create_error_window(message, window_activity):
    error_layout = [
        [sg.Text(f'Error: {message}', key='error_message')],
        [sg.Button('Back')]
    ]
    error_window = sg.Window('Error', error_layout, modal=True)
    window_activity = set_active_window('error', window_activity)
    return error_window, window_activity

# returns a list of template names for the run templates menu
def get_template_names(current_templates):
    template_names = []
    for key in current_templates:
        template_names.append(key)
    return template_names 

# executes the configuration from the run config
def exec_config(run_config, main_window):
    project_name = run_config['project_name']
    task_name = run_config['task_name']
    task_type = run_config['task_type']
    remote_url = run_config['repo']
    current_branch = run_config['branch']
    path = run_config['path']
    script = run_config['script']
    queue = run_config['queue']
    tags = run_config['tags']
    create_populate = CreateAndPopulate(
        project_name=project_name,
        task_name=task_name,
        task_type=task_type,
        repo=remote_url,
        branch=current_branch,
        script=script,
        verbose=True,
    )
    create_populate.create_task()
    create_populate.task._set_runtime_properties({"_CLEARML_TASK": True})
    task_id = create_populate.get_id()
    Task.enqueue(create_populate.task, queue_name=queue)
    if tags != ['']:
        create_populate.task.set_tags(tags)
    main_window['exec_complete_text1'].update(f"New task created id={task_id}")
    main_window['exec_complete_text2'].update(f"Task id={task_id} sent for execution on queue {queue}")
    main_window['exec_layout'].update(visible=False)
    main_window['exec_complete_layout'].update(visible=True)
    return create_populate.task