import PySimpleGUI as sg
from clearml import Task
from clenv.cli.config.config_manager import ConfigManager
from git import Repo
from os.path import isfile
import os, json
from utils import *

'''
App class:

Stores important variables such as:
  - the main window object
  - a standby window
  - config_manager, a ConfigManager object built from the clenv config index 
    file
  - url, the url string for the clearml experiment
  - run_config, a dictionary of information needed to remotely execute an 
    experiment in clearml
  - opt_config, a dictionary of information needed to run a hyperparameter 
    optimization experiment in clearml
  - numeric_params, the parameters from the given clearml experiment that are 
    numerical
  - discrete_params, the parameters from the given clearml experiment that are 
    discrete

The functions are organized in the same order they appear in the main loop in 
clenv_gui.py. The only exceptions are action_success and create_error_message,
which simply create a popup window to let the user know that their action was 
successful or if there was an error respectively.
'''
class App():
    def __init__(self, window):
        self.window = window
        self.standby_window = None
        self.config_manager = ConfigManager('~/.clenv-config-index.json')
        self.url = ''
        self.run_config = {}
        self.opt_config = {}
        self.numeric_params = {}
        self.discrete_params = []

    # initializes the home screen
    def task_exec(self):
        if not isfile('./task_templates.json'):
            with open('task_templates.json', 'w') as f:
                json.dump({"Remote Execution":{},
                           "Model Optimization":{}}, 
                           f, indent=4)
        with open("task_templates.json", "r") as f:
            current_templates = json.load(f)
        template_names = get_template_names(current_templates)
        self.window['template_chosen'].update(values=template_names)

    # main menu controllers      
    def run_template_new(self):
        queue_list = get_queue_list()
        self.window['queue_list'].update(values=queue_list)
        self.window['save_as_template'].update(False)
        self.window['main_layout'].update(visible=False)
        self.window['exec_layout'].update(visible=True)

    def model_opt(self):
        queue_list = get_queue_list()
        self.window['opt_queue'].update(values=queue_list)
        self.window['main_layout'].update(visible=False)
        self.window['model_opt_layout'].update(visible=True)

    def run_template_template(self, main_values):
        if (main_values['template_chosen'] != {} and 
            main_values['template_chosen'] != []):

            template = main_values['template_chosen'][0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            category = template.split(': ')[0]
            template_name = template.split(': ')[-1]

            if category == 'Remote Execution':
                template = current_templates["Remote Execution"][template_name]
                queue_list = get_queue_list()
                self.window['queue_list'].update(values=queue_list)
                queue = get_queue_from_name(template['queue'], queue_list)
                self.window['queue_list'].update(queue)
                self.window['task_types'].update(f'{template["task_type"]}')
                self.window['task_name'].update(f'{template["task_name"]}')
                self.window['path'].update(f'{template["path"]}')
                self.window['save_as_template'].update(False)
                self.window['main_layout'].update(visible=False)
                self.window['exec_layout'].update(visible=True)
            elif category == 'Model Optimization':
                template = current_templates["Model Optimization"][template_name]

                opt_queue = template['opt_queue']
                opt_name = template['opt_name']
                opt_project = template['opt_project']
                task_name_for_opt = template['task_name_for_opt']
                project_name_for_opt = template['project_name_for_opt']
                self.opt_config = {
                    'opt_name':opt_name,
                    'opt_project':opt_project,
                    'task_name_for_opt':task_name_for_opt,
                    'project_name_for_opt':project_name_for_opt,
                    'opt_queue':opt_queue
                    }
                task = Task.get_task(project_name=project_name_for_opt, 
                                     task_name=task_name_for_opt)
        
                raw_params = task.get_parameters_as_dict()
                params = get_numeric_discrete_params(raw_params)
                self.numeric_params, self.discrete_params = params
        
                raw_scalars = task.get_last_scalar_metrics()
                scalars = []
                for scalar in raw_scalars:
                    scalars.append(scalar)
        
                param_opt_layout = get_param_opt_layout(self.opt_config,
                                                        self.numeric_params, 
                                                        self.discrete_params)
                self.standby_window = sg.Window('Parameter Optimization', 
                                                layout=param_opt_layout, 
                                                modal=True,
                                                finalize=True)
                self.standby_window['metric_to_optimize'].update(values=scalars)
                queue_list = get_queue_list()
                self.standby_window['opt_child_queue'].update(values=queue_list)
                
                param_ranges = template['param_ranges']
                for param_name in param_ranges:
                    params = param_ranges[param_name]
                    if isinstance(params, dict):
                        min_value=params['min']
                        max_value=params['max']
                        step_size=params['step']
                        self.standby_window[f'{param_name}_min'].update(min_value)
                        self.standby_window[f'{param_name}_max'].update(max_value)
                        self.standby_window[f'{param_name}_step'].update(step_size)
                    elif isinstance(params, list):
                        values_str = ''
                        num_values = len(params)
                        for index in range(num_values):
                            val = params[index]
                            if index != num_values - 1:
                                values_str += f'{val},'
                            else:
                                values_str += f'{val}'
                        self.standby_window[f'{param_name}_values'].update(values_str)

                for param_name in ["max_number_of_concurrent_tasks",
                              "save_top_k_tasks_only",
                              "time_limit_per_job",
                              "pool_period_min",
                              "total_max_jobs",
                              "min_iteration_per_job",
                              "max_iteration_per_job",
                              "total_time_limit"]:
                    param_value = template[param_name]
                    if param_value == None:
                        param_value = ''
                    else:
                        param_value = str(param_value)
                    self.standby_window[param_name].update(param_value)
                
                self.standby_window['metric_to_optimize'].update(values=scalars)
                self.standby_window['metric_to_optimize'].update(
                    f'{template["metric_to_optimize"]}')
                if template['min_metric']:
                    self.standby_window['min_metric'].update(value=True)
                else:
                    self.standby_window['max_metric'].update(value=False)
                queue_list = get_queue_list()
                self.standby_window['opt_child_queue'].update(values=queue_list)
                queue = get_queue_from_name(template['opt_child_queue'], queue_list)
                self.standby_window['opt_child_queue'].update(queue)
                main_window = self.window
                self.window = self.standby_window
                self.standby_window = main_window
        else:
            self.create_error_window('no template selected')

    def run_template_delete(self, main_values):
        if (main_values['template_chosen'] != {} and 
            main_values['template_chosen'] != []):

            template = main_values['template_chosen'][0]
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            category = template.split(': ')[0]
            template_name = template.split(': ')[-1]
            current_templates[category].pop(template_name)
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            self.window['template_chosen'].update(values=template_names)
        else:
            self.create_error_window('no template selected')

    def config(self):
        if not self.config_manager.profile_has_initialized():
            profile_name = sg.popup_get_text('Please input a profile name:', 
                                             title='Profile Creation')
            self.config_manager.initialize_profile(f'{profile_name}')
            self.window['main_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)
        else:
            self.window['main_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)

    # exec controllers
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
        path = main_values['path']
        if not isfile(path):
            self.create_error_window('must input valid path')
            return
        raw_queue_info = main_values['queue_list']
        task_type = main_values['task_types']
        task_name = main_values['task_name']
        raw_tags = main_values['tags']
        queue, num_idle_workers = get_queue_info(raw_queue_info)
        try:
            dir_path = os.path.dirname(path)
            repo = Repo(f'{dir_path}')
        except:
            self.create_error_window(
                'no git repository detected \nat specified file directory')
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
            template_name = sg.popup_get_text(
                'Please input a template name:', title='Template Creation')
            if template_name == '':
                sg.popup('No template name given', title='Error')
                return
            elif template_name == None:
                return
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            current_templates["Remote Execution"][template_name] = self.run_config
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            self.window['template_chosen'].update(values=template_names)
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
        self.window['tags'].update('')
        self.window['save_as_template'].update(False)
        self.window['exec_complete_layout'].update(visible=False)
        self.window['main_layout'].update(visible=True)

    # model optimization controllers
    def model_opt_confirm(self, values):
        if check_blank_options_model_opt(values):
            self.create_error_window('one or more options is blank')
            return
        raw_queue_info = values['opt_queue']
        opt_queue, num_idle_workers = get_queue_info(raw_queue_info)
        opt_name = values['opt_name']
        opt_project = values['opt_project']
        task_name_for_opt = values['task_name_for_opt']
        project_name_for_opt = values['project_name_for_opt']
        self.opt_config = {
            'opt_name':opt_name,
            'opt_project':opt_project,
            'task_name_for_opt':task_name_for_opt,
            'project_name_for_opt':project_name_for_opt,
            'opt_queue':opt_queue
            }
        task = Task.get_task(project_name=project_name_for_opt, 
                             task_name=task_name_for_opt)

        raw_params = task.get_parameters_as_dict()
        params = get_numeric_discrete_params(raw_params)
        self.numeric_params, self.discrete_params = params

        raw_scalars = task.get_last_scalar_metrics()
        scalars = []
        for scalar in raw_scalars:
            scalars.append(scalar)

        param_opt_layout = get_param_opt_layout(self.opt_config, 
                                                self.numeric_params, 
                                                self.discrete_params)
        self.standby_window = self.window
        self.window = sg.Window('Parameter Optimization', 
                                layout=param_opt_layout, 
                                modal=True,
                                finalize=True)
        self.window['metric_to_optimize'].update(values=scalars)
        queue_list = get_queue_list()
        self.window['opt_child_queue'].update(values=queue_list)

    def model_opt_back(self):
        self.window['model_opt_layout'].update(visible=False)
        self.window['main_layout'].update(visible=True)
        self.window['opt_name'].update('')
        self.window['task_name_for_opt'].update('')
        self.window['project_name_for_opt'].update('')
        with open("task_templates.json", "r") as f:
            current_templates = json.load(f)
        template_names = get_template_names(current_templates)
        self.window['template_chosen'].update(values=template_names)
    
    def param_opt_confirm(self, values):
        if check_blank_options_param_opt(values):
            self.create_error_window('one of the required arguments is blank')
            return
        if check_alpha_chars_param_opt(values):
            self.create_error_window(
                'one or more "Default Parameter" arguments is not numeric')
            return
        
        raw_queue_info = values['opt_child_queue']
        opt_child_queue, num_idle_workers = get_queue_info(raw_queue_info)
        self.opt_config['opt_child_queue'] = opt_child_queue

        param_ranges = {}
        
        for param in self.numeric_params:
            min = values[f'{param}_min']
            max = values[f'{param}_max']
            step = values[f'{param}_step']

            if min == '' or max == '' or step == '':
                continue
            else:
                type = self.numeric_params[param]
                param_ranges[param] = {
                    'min':type(min),
                    'max':type(max),
                    'step':type(step)
                }
        for param in self.discrete_params:
            discrete_values = values[f'{param}_values']

            if discrete_values == '':
                continue
            else:
                discrete_value_list = discrete_values.split(',')

                corrected_discrete_value_list = []
                for value in discrete_value_list:
                    if value == 'true' or value == 'True':
                        corrected_value = True
                    elif value == 'false' or value == 'False':
                        corrected_value = False
                    else:
                        corrected_value = value
                    corrected_discrete_value_list.append(corrected_value)
                
                param_ranges[param] = corrected_discrete_value_list
        
        self.opt_config['param_ranges'] = param_ranges
        
        default_params = [
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

        for param in default_params:
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
        
        # for key in self.opt_config:
        #     value = self.opt_config[key]
        #     print(f'{key}:{value}\n')

        with open('optimizer.py', 'r') as optimizer:
            lines = optimizer.readlines()
        lines.append(f'exec_opt_config({self.opt_config})')
        with open('optimizer.py', 'w') as optimizer:
            optimizer.writelines(lines)
            optimizer.close()
        
        if values['param_opt_save_as_template']:
            template_name = sg.popup_get_text(
                'Please input a template name:', title='Template Creation')
            if template_name == '':
                sg.popup('No template name given', title='Error')
                return
            elif template_name == None:
                return
            with open("task_templates.json", "r") as f:
                current_templates = json.load(f)
            current_templates["Model Optimization"][template_name] = self.opt_config
            with open("task_templates.json", "w") as f:
                json.dump(current_templates, f, indent=4)
            template_names = get_template_names(current_templates)
            self.standby_window['template_chosen'].update(values=template_names)
        
        task, task_id, opt_queue = exec_opt_config(self.opt_config)
        self.url = task.get_output_log_web_page()
        self.standby_window['model_opt_complete_text1'].update(
            f"New task created id={task_id}")
        self.standby_window['model_opt_complete_text2'].update(
            f"Execution on queue {opt_queue}")
        self.standby_window['model_opt_layout'].update(visible=False)
        self.standby_window['main_layout'].update(visible=False)
        self.standby_window['model_opt_complete_layout'].update(visible=True)
        self.window.close()
        self.window = self.standby_window

        with open('optimizer.py', 'r') as optimizer:
            lines = optimizer.readlines()
        lines.pop()
        with open('optimizer.py', 'w') as optimizer:
            optimizer.writelines(lines)
            optimizer.close()

    def param_opt_cancel(self):
        self.window.close()
        self.window = self.standby_window
        with open("task_templates.json", "r") as f:
            current_templates = json.load(f)
        template_names = get_template_names(current_templates)
        self.window['template_chosen'].update(values=template_names)
    
    def model_opt_complete_back(self):
        self.window['model_opt_complete_layout'].update(visible=False)
        self.window['main_layout'].update(visible=True)

    # config controllers
    def config_confirm(self, main_values):
        option = main_values['config_options']
        if option == '':
            return True
        # option_layout is the string key associated with the layout of the 
        #   option selected in the dropdown menu
        option_layout = f'config_{option.split(" ")[0].lower()}_layout'
        active_profile = self.config_manager.get_active_profile()[0]
        non_active_profiles = self.config_manager.get_non_active_profiles()
        non_active_profile_names = get_non_active_profile_names(
            non_active_profiles)
        profile_list = get_profile_list(active_profile, non_active_profiles)
        # reset layout whenever selected
        if option_layout == 'config_checkout_layout':
            self.window['checkout_active_profile'].update(
                f'Active Profile: {active_profile["profile_name"]}')
            self.window['checkout_non_active_profiles'].update(
                values=non_active_profile_names)
        elif option_layout == 'config_create_layout':
            self.window['new_profile_name'].update('')
        elif option_layout == 'config_delete_layout':
            self.window['delete_non_active_profiles'].update(
                values=non_active_profile_names)
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
        self.window[f'{option_back.split("back")[0]}layout'].update(
            visible=False)
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
            self.config_manager.rename_profile(
                profile_to_rename, profile_rename)
            self.action_success()
            self.window['config_rename_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)

    def config_configure_confirm(self, main_values):
        profile_to_config = main_values['profile_to_config']
        config = main_values['multiline_config']
        try:
            self.config_manager.reinitialize_api_config(
                profile_to_config, config)
            self.action_success()
            self.window['config_configure_layout'].update(visible=False)
            self.window['config_layout'].update(visible=True)
        except:
            self.create_error_window('invalid configuration format')

    # creates an action success window
    def action_success(self):
        sg.popup('Action completed successfully!', title='Action Success!')
        self.window['config_options'].update('')

    # creates an error window
    def create_error_window(self, message):
        sg.popup(f'Error: {message}', title='Error')
