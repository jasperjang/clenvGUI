import PySimpleGUI as sg
from clearml import Task
from clearml.backend_interface.task.populate import CreateAndPopulate
from clenv.cli.queue.queue_manager import QueueManager
from git import Repo
from os.path import isfile
import os, json

################################################################################
######                             Classes                                ######
################################################################################

'''
App class:

To store global variables such as:
- windows, a dictionary of window name keys pointing to ActiveWindow objects
- config_manager, a ConfigManager object built from the clenv config index file
- URL, the url string for the clearml experiment
- run_config, a dictionary of information needed to run an experiment in clearml

Mostly contains functions that modify elements and valulues in the PySimpleGUI 
window
'''
class App():
    def __init__(self, windows, config_manager, URL, run_config):
        self.windows = windows
        self.main_window = self.windows['CLENV']
        self.config_manager = config_manager
        self.url = URL
        self.run_config = run_config
    
    def get_active_window(self):
        for window in self.windows.values():
            if window.active:
                return window
            
    # creates an action success window
    def action_success(self):
        self.main_window.window['config_options'].update('')
        action_successful_layout = [
            [sg.Text('Action completed successfully!')]
        ]
        action_successful_window = ActiveWindow(sg.Window('Action Successful', action_successful_layout, modal=True), active=True)
        self.windows[action_successful_window.name] = action_successful_window
        self.main_window.set_inactive()

    # creates an error window
    def create_error_window(self, message):
        error_layout = [
            [sg.Text(f'Error: {message}', key='error_message')],
            [sg.Button('Back')]
        ]
        error_window = ActiveWindow(sg.Window('Error', error_layout, modal=True), active=True)
        self.windows[error_window.name] = error_window
        self.main_window.set_inactive()

    def task_exec(self):
        if not isfile('./task_templates.json'):
            with open('task_templates.json', 'w') as f:
                json.dump({}, f, indent=4)
        with open("task_templates.json", "r") as f:
            current_templates = json.load(f)
        template_names = get_template_names(current_templates)
        self.main_window.window['template_chosen'].update(values=template_names)
        self.main_window.window['main_layout'].update(visible=False)
        self.main_window.window['run_template_layout'].update(visible=True)

    def config(self):
        if not self.config_manager.profile_has_initialized():
            new_config_layout = [
                [sg.Text('Please input a profile name:')],
                [sg.InputText()],
                [sg.Button('Confirm')]
            ]
            new_config_window = ActiveWindow(sg.Window('Profile Creation', new_config_layout, modal=True), active=True)
            self.windows[new_config_window.name] = new_config_window
            self.main_window.set_inactive()
        else:
            self.main_window.window['main_layout'].update(visible=False)
            self.main_window.window['config_layout'].update(visible=True)

    def config_confirm(self, main_values):
        option = main_values['config_options']
        if option == '':
            return True
        # option_layout is the string key associated with the layout of the option selected in the dropdown menu
        option_layout = f'config_{option.split(" ")[0].lower()}_layout'
        active_profile = self.config_manager.get_active_profile()[0]
        non_active_profiles = self.config_manager.get_non_active_profiles()
        non_active_profile_names = get_non_active_profile_names(non_active_profiles)
        profile_list = get_profile_list(active_profile, non_active_profiles)
        # reset layout whenever selected
        if option_layout == 'config_checkout_layout':
            self.main_window.window['checkout_active_profile'].update(f'Active Profile: {active_profile["profile_name"]}')
            self.main_window.window['checkout_non_active_profiles'].update(values=non_active_profile_names)
        elif option_layout == 'config_create_layout':
            self.main_window.window['new_profile_name'].update('')
        elif option_layout == 'config_delete_layout':
            self.main_window.window['delete_non_active_profiles'].update(values=non_active_profile_names)
            self.main_window.window['delete_non_active_profiles'].update('')
        elif option_layout == 'config_list_layout':
            profile_string = get_profile_string(profile_list)
            self.main_window.window['profile_list'].update(profile_string)
        elif option_layout == 'config_rename_layout':
            self.main_window.window['profile_list_menu'].update(values=profile_list)
            self.main_window.window['profile_rename'].update('')
        elif option_layout == 'config_configure_layout':
            self.main_window.window['profile_to_config'].update(values=profile_list)
            self.main_window.window['profile_to_config'].update('')
            self.main_window.window['multiline_config'].update('')
        self.main_window.window['config_layout'].update(visible=False)
        self.main_window.window[option_layout].update(visible=True)

    def config_back(self):
        self.main_window.window['config_options'].update('')
        self.main_window.window['config_layout'].update(visible=False)
        self.main_window.window['main_layout'].update(visible=True)

    def option_back(self, option_back):
        self.main_window.window[f'{option_back.split("back")[0]}layout'].update(visible=False)
        self.main_window.window['config_options'].update('')
        self.main_window.window['config_layout'].update(visible=True)

    def config_checkout_confirm(self, main_values):
        profileName = main_values['checkout_non_active_profiles']
        if self.config_manager.has_profile(profile_name=profileName):
            self.config_manager.set_active_profile(profileName)
            self.action_success()
            self.main_window.window['config_checkout_layout'].update(visible=False)
            self.main_window.window['config_layout'].update(visible=True)
    
    def config_create_confirm(self, main_values):
        new_profile_name = main_values['new_profile_name']
        if self.config_manager.has_profile(profile_name=new_profile_name):
            self.create_error_window('profile already exists')
        else:
            self.config_manager.create_profile(new_profile_name)
            self.action_success()
            self.main_window.window['config_create_layout'].update(visible=False)
            self.main_window.window['config_layout'].update(visible=True)

    def config_delete_confirm(self, main_values):
        profile_to_delete = main_values['delete_non_active_profiles']
        self.config_manager.delete_profile(profile_to_delete)
        self.action_success()
        self.main_window.window['config_delete_layout'].update(visible=False)
        self.main_window.window['config_layout'].update(visible=True)

    def config_rename_confirm(self, main_values):
        profile_to_rename = main_values['profile_list_menu']
        profile_rename = main_values['profile_rename']
        active_profile = self.config_manager.get_active_profile()[0]
        non_active_profiles = self.config_manager.get_non_active_profiles()
        profile_list = get_profile_list(active_profile, non_active_profiles)
        if profile_rename in profile_list:
            self.create_error_window('profile name is already taken')
        elif profile_to_rename == '' or profile_rename == '':
            self.create_error_window('one or more options is blank')
        else:
            self.config_manager.rename_profile(profile_to_rename, profile_rename)
            self.action_success()
            self.main_window.window['config_rename_layout'].update(visible=False)
            self.main_window.window['config_layout'].update(visible=True)

    def config_configure_confirm(self, main_values):
        profile_to_config = main_values['profile_to_config']
        config = main_values['multiline_config']
        try:
            self.config_manager.reinitialize_api_config(profile_to_config, config)
            self.action_success()
            self.main_window.window['config_configure_layout'].update(visible=False)
            self.main_window.window['config_layout'].update(visible=True)
        except:
            self.create_error_window('invalid configuration format')

    def run_template_new(self):
        queue_list = get_queue_list()
        self.main_window.window['queue_list'].update(values=queue_list)
        self.main_window.window['save_as_template'].update(False)
        self.main_window.window['run_template_layout'].update(visible=False)
        self.main_window.window['exec_layout'].update(visible=True)

    def run_template_template(self, main_values):
        if main_values['template_chosen'] != {} and main_values['template_chosen'] != []:
            queue_list = get_queue_list()
            self.main_window.window['queue_list'].update(values=queue_list)
            template_name = main_values['template_chosen'][0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            template = current_templates[template_name]
            queue_list = get_queue_list()
            queue = get_queue_from_name(template['queue'], queue_list)
            self.main_window.window['queue_list'].update(queue)
            self.main_window.window['task_types'].update(f'{template["task_type"]}')
            self.main_window.window['task_name'].update(f'{template["task_name"]}')
            self.main_window.window['path'].update(f'{template["path"]}')
            self.main_window.window['save_as_template'].update(False)
            self.main_window.window['run_template_layout'].update(visible=False)
            self.main_window.window['exec_layout'].update(visible=True)
        else:
            self.create_error_window('no template selected')

    def run_template_delete(self, main_values):
        if main_values['template_chosen'] != {} and main_values['template_chosen'] != []:
            template_name = main_values['template_chosen'][0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            current_templates.pop(template_name)
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            self.main_window.window['template_chosen'].update(values=template_names)
        else:
            self.create_error_window('no template selected')

    def run_template_back(self):
        self.main_window.window['run_template_layout'].update(visible=False)
        self.main_window.window['main_layout'].update(visible=True)

    def exec_back(self):
        self.main_window.window['exec_layout'].update(visible=False)
        self.main_window.window['run_template_layout'].update(visible=True)
        self.main_window.window['queue_list'].update('')
        self.main_window.window['task_types'].update('')
        self.main_window.window['task_name'].update('')
        self.main_window.window['path'].update('/')

    def exec_confirm(self, main_values):
        raw_queue_info = main_values['queue_list']
        task_type = main_values['task_types']
        task_name = main_values['task_name']
        path = main_values['path']
        raw_tags = main_values['tags']
        if check_blank_options(main_values):
            self.create_error_window('one or more options is blank')
        elif not isfile(path):
            self.create_error_window('must input valid path')
        else:
            queue, num_idle_workers, total_workers = get_queue_info(raw_queue_info)
            try:
                dir_path = os.path.dirname(path)
                repo = Repo(f'{dir_path}')
            except:
                self.create_error_window('no git repository detected \nat specified file directory')
            # Read the git information from current directory
            current_branch = repo.head.reference.name
            remote_url = repo.remotes.origin.url
            project_name = remote_url.split("/")[-1].split(".")[0]
            script = os.path.basename(path)
            tags = raw_tags.split(',')
            self.run_config = {
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
                self.windows[new_template_window.name] = new_template_window
                self.main_window.set_inactive()
            else:
                task = exec_config(self.run_config, self.main_window.window)
                self.url = task.get_output_log_web_page()

    def exec_complete_back(self):
        self.main_window.window['queue_list'].update('')
        self.main_window.window['task_types'].update('')
        self.main_window.window['task_name'].update('')
        self.main_window.window['path'].update('/')
        self.main_window.window['save_as_template'].update(False)
        self.main_window.window['exec_complete_layout'].update(visible=False)
        self.main_window.window['run_template_layout'].update(visible=True)

'''
ActiveWindow class:

Similar to the PySimpleGUI Window class, but also stores the window activity 
bool, which I use to make sure only one window is interacted with at a time
'''
class ActiveWindow():
    def __init__(self, window, active):
        self.name = window.Title
        self.window = window
        self.active = active

    def __repr__(self):
        return str(self.active)

    def set_active(self):
        self.active = True

    def set_inactive(self):
        self.active = False

################################################################################
######                         Helper Functions                           ######
################################################################################

# returns readable list of available queues
def get_queue_list():
    queue_manager = QueueManager()
    available_queues = queue_manager.get_available_queues()
    queue_list = []
    for queue in available_queues:
        name = queue['name']
        idle_workers = [worker['name'] for worker in queue['workers'] if worker['task'] is None]
        if idle_workers == []:
            idle_workers = 'NONE'
        total_workers = len(queue['workers'])
        queue_list.append(f"{name} - idle workers: {idle_workers} - total workers: {total_workers}")
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