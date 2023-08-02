import PySimpleGUI as sg
from clearml import Task
from clearml.backend_interface.task.populate import CreateAndPopulate
from clenv.cli.queue.queue_manager import QueueManager
from clenv.cli.config.config_manager import ConfigManager
from git import Repo
from os.path import isfile
import os, json

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

Mostly contains functions that modify elements and values in the PySimpleGUI 
window
'''
class App():
    def __init__(self, window):
        self.window = window
        self.standby_window = None
        self.config_manager = ConfigManager('~/.clenv-config-index.json')
        self.url = ''
        self.run_config = {}
        self.opt_config = {}
        self.numeric_params = []
            
    # creates an action success window
    def action_success(self):
        sg.popup('Action completed successfully!', title='Action Success!')
        self.window['config_options'].update('')

    # creates an error window
    def create_error_window(self, message):
        sg.popup(f'Error: {message}', title='Error')

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
        if check_blank_options_exec(main_values):
            self.create_error_window('one or more options is blank')
            return
        if not isfile(path):
            self.create_error_window('must input valid path')
            return
        raw_queue_info = main_values['queue_list']
        task_type = main_values['task_types']
        task_name = main_values['task_name']
        path = main_values['path']
        raw_tags = main_values['tags']
        queue, num_idle_workers, total_workers = get_queue_info(raw_queue_info)
        try:
            dir_path = os.path.dirname(path)
            repo = Repo(f'{dir_path}')
        except:
            self.create_error_window('no git repository detected \nat specified file directory')
            return
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
        if check_blank_options_model_opt(values):
            self.create_error_window('one or more options is blank')
            return
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

        raw_params = task.get_parameters_as_dict()
        self.numeric_params = get_numeric_params(raw_params)

        raw_scalars = task.get_last_scalar_metrics()
        scalars = []
        for scalar in raw_scalars:
            scalars.append(scalar)

        params_layout = [[sg.Text('Parameter:', font='Ariel 14 bold')]]
        min_layout = [[sg.Text('Min:', font='Ariel 14 bold')]]
        max_layout = [[sg.Text('Max:', font='Ariel 14 bold')]]
        step_layout = [[sg.Text('Step:', font='Ariel 14 bold')]]

        for param in self.numeric_params:
            params_layout.append(
                            [sg.Text(param), 
                             sg.Push(), 
                             sg.Text(str(self.numeric_params[param]))])
            min_layout.append(
                [sg.InputText(size=(5,1), key=f'{param}_min')])
            max_layout.append(
                [sg.InputText(size=(5,1), key=f'{param}_max')])
            step_layout.append(
                [sg.InputText(size=(5,1), key=f'{param}_step')])

        left_param_opt_layout = [
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
            ]
        ]
        right_param_opt_layout = [
            [sg.Text()],
            [
                sg.Text('*', text_color='red'),
                sg.Text('Metric to Optimize:'),
                sg.Push(), 
                sg.OptionMenu(scalars, key='metric_to_optimize', size=(25,1))
            ],
            [
                sg.Text('*', text_color='red'),
                sg.Text('Maximize or minimize the metric?'), 
                sg.Push(),
                sg.Radio('Minimize', 'RADIO1', key='min_metric'),
                sg.Radio('Maximize', 'RADIO1', key='max_metric')
            ],
            [
                sg.Text('*', text_color='red'),
                sg.Text('Max number of concurrent tasks:'),
                sg.Push(), 
                sg.InputText('2', size=(5,1), key='max_number_of_concurrent_tasks')
            ],
            [
                sg.Text('Number of top tasks to save:'), 
                sg.Push(),
                sg.InputText('5', size=(5,1), key='save_top_k_tasks_only')
            ],
            [
                sg.Text('Time limit per job in minutes:'),
                sg.Push(), 
                sg.InputText('10', size=(5,1), key='time_limit_per_job')
            ],
            [
                sg.Text('*', text_color='red'),
                sg.Text('Time interval to check on the experiments in minutes:'),
                sg.Push(), 
                sg.InputText('0.2', size=(5,1), key='pool_period_min')
            ],
            [
                sg.Text('Maximum number of jobs to launch for the optimization:'), 
                sg.Push(),
                sg.InputText('10', size=(5,1), key='total_max_jobs')
            ],
            [
                sg.Text('Minimum number of iterations for an experiment:'), 
                sg.Push(),
                sg.InputText('10', size=(5,1), key='min_iteration_per_job')
            ],
            [
                sg.Text('Maximum number of iterations for an experiment:'),
                sg.Push(), 
                sg.InputText('30', size=(5,1), key='max_iteration_per_job')
            ],
            [
                sg.Text('Total time limit for the optimization in minutes:'),
                sg.Push(), 
                sg.InputText('120', size=(5,1), key='total_time_limit')
            ],
            [sg.Text()],
            [sg.Text('* required argument', text_color='red')]
        ]
        param_opt_layout = [
            [
                sg.Push(), 
                sg.Text('Hyperparameter Optimization', font='Ariel 24 bold'),
                sg.Push()
            ],
            [
                sg.Column(left_param_opt_layout), 
                sg.Column(right_param_opt_layout)
            ],
            [sg.Text('')],
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
        if check_blank_options_param_opt(values):
            self.create_error_window('one of the required arguments is blank')
            return
        if check_alpha_chars_param_opt(values):
            self.create_error_window('one or more arguments is not numeric')
            return

        param_ranges = {}
        for param in self.numeric_params:
            min = values[f'{param}_min']
            max = values[f'{param}_max']
            step = values[f'{param}_step']

            if min == '' or max == '' or step == '':
                continue

            type = self.numeric_params[param]
            param_ranges[param] = {
                'min':type(min),
                'max':type(max),
                'step':type(step)
            }
        
        other_params = [
            'metric_to_optimize',
            'min_metric',
            'max_number_of_concurrent_tasks',
            'save_top_k_tasks_only',
            'time_limit_per_job',
            'pool_period_min',
            'total_max_jobs',
            'min_iteration_per_job',
            'max_iteration_per_job',
            'total_time_limit'
        ]

        for param in other_params:
            value = values[param]
            if value != '':
                if param in ('max_number_of_concurrent_tasks',
                             'save_top_k_tasks_only',
                             'total_max_jobs',
                             'min_iteration_per_job',
                             'max_iteration_per_job'):
                    value = int(value)
                elif param in ('time_limit_per_job',
                               'pool_period_min',
                               'total_time_limit'):
                    value = float(value)
                self.opt_config[param] = value
            else:
                self.opt_config[param] = None
        self.opt_config['param_ranges'] = param_ranges
        
        with open('optimizer.py', 'r') as optimizer:
            lines = optimizer.readlines()
        lines.append(f'exec_opt_config({self.opt_config})')
        with open('optimizer.py', 'w') as optimizer:
            optimizer.writelines(lines)
            optimizer.close()
        
        opt_name = self.opt_config['opt_name']
        opt_project = self.opt_config['opt_project']
        queue = self.opt_config['queue']
        create_populate = CreateAndPopulate(
            project_name=opt_project,
            task_name=opt_name,
            task_type=Task.TaskTypes.optimizer,
            script='optimizer.py',
        )
        create_populate.create_task()
        create_populate.task._set_runtime_properties({"_CLEARML_TASK": True})
        task_id = create_populate.get_id()
        Task.enqueue(create_populate.task, queue_name=queue)
        self.url = create_populate.task.get_output_log_web_page()
        self.standby_window['model_opt_complete_text1'].update(f"New task created id={task_id}")
        self.standby_window['model_opt_complete_text2'].update(f"Execution on queue {queue}")
        self.window.close()
        self.window = self.standby_window
        self.window['model_opt_layout'].update(visible=False)
        self.window['model_opt_complete_layout'].update(visible=True)

        with open('optimizer.py', 'r') as optimizer:
            lines = optimizer.readlines()
        lines.pop()
        with open('optimizer.py', 'w') as optimizer:
            optimizer.writelines(lines)
            optimizer.close()

    def param_opt_cancel(self):
        self.window.close()
        self.window = self.standby_window
    
    def model_opt_complete_back(self):
        self.window['model_opt_complete_layout'].update(visible=False)
        self.window['main_layout'].update(visible=True)

################################################################################
######                         Helper Functions                           ######
################################################################################

def get_numeric_params(raw_params):
    numeric_params = {}
    for category in raw_params:
        params = raw_params[category]
        for param in params:
            value = params[param]
            label = f'{category}/{param}'
            if type(value) == str:
                if value.isdigit():
                    numeric_params[label] = int
                elif value.replace('.', "").isdigit():
                    numeric_params[label] = float
            else:
                nested_params = params[param]
                for nested_param in nested_params:
                    value = nested_params[nested_param]
                    label = f'{category}/{param}/{nested_param}'
                    if type(value) == str:
                        if value.isdigit():
                            numeric_params[label] = int
                        elif value.replace('.', "").isdigit():
                            numeric_params[label] = float
    return numeric_params

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
def check_blank_options_exec(values):
    if (values['queue_list'] == '' or
        values['task_types'] == '' or
        values['task_name'] == '' or
        values['path'] == ''):
        return True
    return False

def check_blank_options_model_opt(values):
    if (values['opt_queue_list'] == '' or
        values['opt_name'] == '' or
        values['opt_project'] == '' or
        values['task_name_for_opt'] == '' or 
        values['project_name_for_opt'] == ''):
        return True
    return False

def check_blank_options_param_opt(values):
    if (values['metric_to_optimize'] == '' or
        values['pool_period_min'] == '' or 
        values['max_number_of_concurrent_tasks'] == ''):
        return True
    if values['min_metric'] == False and values['max_metric'] == False:
        return True
    return False

def check_alpha_chars_param_opt(values):
    for param in ('max_number_of_concurrent_tasks',
                  'save_top_k_tasks_only',
                  'total_max_jobs',
                  'min_iteration_per_job',
                  'max_iteration_per_job',
                  'time_limit_per_job',
                  'pool_period_min',
                  'total_time_limit'):
        value = values[param]
        if value.count('.') > 1:
            return True
        if value.isalnum() and not value.isdigit():
            return True
        if not value.replace('.', '', 1).isdigit():
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
    )
    create_populate.create_task()
    create_populate.task._set_runtime_properties({"_CLEARML_TASK": True})
    task_id = create_populate.get_id()
    Task.enqueue(create_populate.task, queue_name=queue)
    if tags != ['']:
        create_populate.task.set_tags(tags)
    window['exec_complete_text1'].update(f"New task created id={task_id}")
    window['exec_complete_text2'].update(f"Execution on queue {queue}")
    window['exec_layout'].update(visible=False)
    window['exec_complete_layout'].update(visible=True)
    return create_populate.task