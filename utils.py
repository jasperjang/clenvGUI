import PySimpleGUI as sg
from clearml import Task
from clearml.backend_interface.task.populate import CreateAndPopulate
from clenv.cli.queue.queue_manager import QueueManager
from git import Repo
from os.path import isfile
import os, json
from optimizer import *

################################################################################
######                             Classes                                ######
################################################################################

'''
App class:

To store global variables such as:
- the main window object
- config_manager, a ConfigManager object built from the clenv config index file
- URL, the url string for the clearml experiment
- run_config, a dictionary of information needed to run an experiment in clearml

Mostly contains functions that modify elements and valulues in the PySimpleGUI 
window
'''
class App():
    def __init__(self, window, standby_window, config_manager, URL, run_config, opt_config):
        self.window = window
        self.standby_window = standby_window
        self.config_manager = config_manager
        self.url = URL
        self.run_config = run_config
            
    # creates an action success window
    def action_success(self):
        sg.popup('Action completed successfully!', title='Action Success!')
        self.window['config_options'].update('')

    # creates an error window
    def create_error_window(self, message):
        sg.popup(message, title='Error')

    def task_exec(self):
        if not isfile('./task_templates.json'):
            with open('task_templates.json', 'w') as f:
                json.dump({}, f, indent=4)
        with open("task_templates.json", "r") as f:
            current_templates = json.load(f)
        template_names = get_template_names(current_templates)
        self.window['template_chosen'].update(values=template_names)

    def config(self):
        if not self.config_manager.profile_has_initialized():
            profile_name = sg.popup_get_text('Please input a profile name:', title='Profile Creation')
            self.config_manager.initialize_profile(f'{profile_name}')
            self.window['main_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)
        else:
            self.window['main_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)

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
            self.window['checkout_active_profile'].update(f'Active Profile: {active_profile["profile_name"]}')
            self.window['checkout_non_active_profiles'].update(values=non_active_profile_names)
        elif option_layout == 'config_create_layout':
            self.window['new_profile_name'].update('')
        elif option_layout == 'config_delete_layout':
            self.window['delete_non_active_profiles'].update(values=non_active_profile_names)
            self.window['delete_non_active_profiles'].update('')
        elif option_layout == 'config_list_layout':
            profile_string = get_profile_string(profile_list)
            self.window['profile_list'].update(profile_string)
        elif option_layout == 'config_rename_layout':
            self.window['profile_list_menu'].update(values=profile_list)
            self.window['profile_rename'].update('')
        elif option_layout == 'config_configure_layout':
            self.window['profile_to_config'].update(values=profile_list)
            self.window['profile_to_config'].update('')
            self.window['multiline_config'].update('')
        self.window['config_layout'].update(visible=False)
        self.window[option_layout].update(visible=True)

    def config_back(self):
        self.window['config_options'].update('')
        self.window['config_layout'].update(visible=False)
        self.window['main_layout'].update(visible=True)

    def option_back(self, option_back):
        self.window[f'{option_back.split("back")[0]}layout'].update(visible=False)
        self.window['config_options'].update('')
        self.window['config_layout'].update(visible=True)

    def config_checkout_confirm(self, main_values):
        profileName = main_values['checkout_non_active_profiles']
        if self.config_manager.has_profile(profile_name=profileName):
            self.config_manager.set_active_profile(profileName)
            self.action_success()
            self.window['config_checkout_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)
    
    def config_create_confirm(self, main_values):
        new_profile_name = main_values['new_profile_name']
        if self.config_manager.has_profile(profile_name=new_profile_name):
            self.create_error_window('profile already exists')
        else:
            self.config_manager.create_profile(new_profile_name)
            self.action_success()
            self.window['config_create_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)

    def config_delete_confirm(self, main_values):
        profile_to_delete = main_values['delete_non_active_profiles']
        self.config_manager.delete_profile(profile_to_delete)
        self.action_success()
        self.window['config_delete_layout'].update(visible=False)
        self.window['config_layout'].update(visible=True)

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
            self.window['config_rename_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)

    def config_configure_confirm(self, main_values):
        profile_to_config = main_values['profile_to_config']
        config = main_values['multiline_config']
        try:
            self.config_manager.reinitialize_api_config(profile_to_config, config)
            self.action_success()
            self.window['config_configure_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)
        except:
            self.create_error_window('invalid configuration format')

    def run_template_new(self):
        queue_list = get_queue_list()
        self.window['queue_list'].update(values=queue_list)
        self.window['save_as_template'].update(False)
        self.window['main_layout'].update(visible=False)
        self.window['exec_layout'].update(visible=True)

    def run_template_template(self, main_values):
        if main_values['template_chosen'] != {} and main_values['template_chosen'] != []:
            queue_list = get_queue_list()
            self.window['queue_list'].update(values=queue_list)
            template_name = main_values['template_chosen'][0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            template = current_templates[template_name]
            queue_list = get_queue_list()
            queue = get_queue_from_name(template['queue'], queue_list)
            self.window['queue_list'].update(queue)
            self.window['task_types'].update(f'{template["task_type"]}')
            self.window['task_name'].update(f'{template["task_name"]}')
            self.window['path'].update(f'{template["path"]}')
            self.window['save_as_template'].update(False)
            self.window['main_layout'].update(visible=False)
            self.window['exec_layout'].update(visible=True)
        else:
            self.create_error_window('No template selected')

    def run_template_delete(self, main_values):
        if main_values['template_chosen'] != {} and main_values['template_chosen'] != []:
            template_name = main_values['template_chosen'][0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            current_templates.pop(template_name)
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            self.window['template_chosen'].update(values=template_names)
        else:
            self.create_error_window('no template selected')

    def exec_back(self):
        with open("task_templates.json", "r") as f:
            current_templates = json.load(f)
        template_names = get_template_names(current_templates)
        self.window['template_chosen'].update(values=template_names)
        self.window['exec_layout'].update(visible=False)
        self.window['main_layout'].update(visible=True)
        self.window['queue_list'].update('')
        self.window['task_types'].update('')
        self.window['task_name'].update('')
        self.window['path'].update('/')
        self.window['tags'].update('')

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
                template_name = sg.popup_get_text('Please input a template name:', title='Template Creation')
                if template_name == '':
                    sg.popup('No template name given', title='Error')
                    return
                elif template_name == None:
                    return
                with open("task_templates.json", "r") as f:
                    current_templates = json.load(f)
                current_templates[template_name] = self.run_config
                with open("task_templates.json", "w") as f:
                    json.dump(current_templates, f, indent=4)
                template_names = get_template_names(current_templates)
                self.window['template_chosen'].update(values=template_names)
                task = exec_config(self.run_config, self.window)
                self.url = task.get_output_log_web_page()
            else:
                task = exec_config(self.run_config, self.window)
                self.url = task.get_output_log_web_page()

    def exec_complete_back(self):
        with open("task_templates.json", "r") as f:
            current_templates = json.load(f)
        template_names = get_template_names(current_templates)
        self.window['template_chosen'].update(values=template_names)
        self.window['queue_list'].update('')
        self.window['task_types'].update('')
        self.window['task_name'].update('')
        self.window['path'].update('/')
        self.window['save_as_template'].update(False)
        self.window['exec_complete_layout'].update(visible=False)
        self.window['main_layout'].update(visible=True)

    def model_opt(self):
        queue_list = get_queue_list()
        self.window['opt_queue_list'].update(values=queue_list)
        self.window['main_layout'].update(visible=False)
        self.window['model_opt_layout'].update(visible=True)
    
    def model_opt_confirm(self, values):
        raw_queue_info = values['opt_queue_list']
        queue, num_idle_workers, total_workers = get_queue_info(raw_queue_info)
        opt_name = values['opt_name']
        opt_project = values['opt_project']
        task_name_for_opt = values['task_name_for_opt']
        project_name_for_opt = values['project_name_for_opt']
        self.opt_config = {
            'opt_name':opt_name,
            'opt_project':opt_project,
            'task_name_for_opt':task_name_for_opt,
            'project_name_for_opt':project_name_for_opt,
            'queue':queue
            }
        task = Task.get_task(project_name=project_name_for_opt, 
                             task_name=task_name_for_opt)
        opt_params = task.get_parameters_as_dict()
        params_layout = [[sg.Text('Parameter:', font='Ariel 14 bold')]]
        min_layout = [[sg.Text('Min:', font='Ariel 14 bold')]]
        max_layout = [[sg.Text('Max:', font='Ariel 14 bold')]]
        step_layout = [[sg.Text('Step:', font='Ariel 14 bold')]]
        num_params = 0
        for category in opt_params:
            for param in opt_params[category]:
                params_layout.append([sg.Text(f'{category}: {param}')])
                min_layout.append([sg.InputText(size=(10,1), key=f'{param}_min')])
                max_layout.append([sg.InputText(size=(10,1), key=f'{param}_max')])
                step_layout.append([sg.InputText(size=(10,1), key=f'{param}_step')])
                num_params += 1

        param_opt_layout = [
            [sg.Text('''
Input a min value, max value, and step size for each parameter 
or leave blank if you do not wish to optimize the parameter.''')],
            [
                sg.Column(params_layout),
                sg.Push(), 
                sg.Column(min_layout),
                sg.Push(), 
                sg.Column(max_layout),
                sg.Push(), 
                sg.Column(step_layout)
            ],
            [sg.Text()],
            [
                sg.Text('Objective Metric Title to Optimize:'),
                sg.Push(), 
                sg.InputText(key='objective_metric_title', size=(25,1))
            ],
            [sg.Text()],
            [
                sg.Text('Objective Metric Series to Optimize:'), 
                sg.Push(),
                sg.InputText(key='objective_metric_series', size=(25,1))
            ],
            [sg.Text()],
            [
                sg.Text('Maximize or minimize the metric?'), 
                sg.Radio('Minimize', 'RADIO1', key='min_metric'),
                sg.Radio('Maximize', 'RADIO1', key='max_metric')
            ],
            [sg.Text()],
            [
                sg.Button('Confirm', key='param_opt_confirm'),
                sg.Button('Cancel', key='param_opt_cancel')
            ]
        ]
        self.standby_window = self.window
        self.window = sg.Window('Parameter Optimization', 
                                layout=param_opt_layout, 
                                modal=True)

    def model_opt_back(self):
        self.window['model_opt_layout'].update(visible=False)
        self.window['main_layout'].update(visible=True)
        self.window['opt_name'].update('')
        self.window['task_name_for_opt'].update('')
        self.window['project_name_for_opt'].update('')
    
    def param_opt_confirm(self, values):
        self.window.close()
        self.window = self.standby_window
        self.window['model_opt_layout'].update(visible=False)
        self.window['model_opt_complete_layout'].update(visible=True)
        exec_opt_config(self.opt_config)

    def param_opt_cancel(self):
        self.window.close()
        self.window = self.standby_window

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
def exec_config(run_config, window):
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
    window['exec_complete_text1'].update(f"New task created id={task_id}")
    window['exec_complete_text2'].update(f"Task id={task_id} sent for execution on queue {queue}")
    window['exec_layout'].update(visible=False)
    window['exec_complete_layout'].update(visible=True)
    return create_populate.task