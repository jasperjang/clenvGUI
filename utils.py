import PySimpleGUI as sg
from clearml import Task
from clearml.backend_interface.task.populate import CreateAndPopulate
from clenv.cli.queue.queue_manager import QueueManager

# detects which parameters are numerical (int or float) and which are discrete 
#   string values, then organizes them into numeric_params and discrete_params
def get_numeric_discrete_params(raw_params):
    numeric_params = {}
    discrete_params = []
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
                    discrete_params.append(label)
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
                        else:
                            discrete_params.append(label)
    return numeric_params, discrete_params

# returns readable list of available queues
def get_queue_list():
    queue_manager = QueueManager()
    available_queues = queue_manager.get_available_queues()
    queue_list = []
    for queue in available_queues:
        name = queue['name']
        idle_workers = [worker['name'] for worker in queue['workers'] 
                        if worker['task'] is None]
        if idle_workers == []:
            num_idle_workers = 'NONE'
        else:
            num_idle_workers = len(idle_workers)
        queue_list.append(
            f"{name}   -   # idle workers: {num_idle_workers}")
    return queue_list

# returns queue name, number of idle workers, and total number of workers from 
#   the queue_list format above
def get_queue_info(queue_list_item):
    print(queue_list_item)
    L = queue_list_item.split('   -   # idle workers: ')
    queue = L[0]
    num_idle_workers = L[1]
    return queue, num_idle_workers

# returns the queue information from the given queue name and queue list
def get_queue_from_name(name, queue_list):
    for queue in queue_list:
        split_queue = queue.split(' ')
        if split_queue[0] == name:
            return queue

# checks if any values in the exec dictionary are empty
def check_blank_options_exec(values):
    if (values['queue_list'] == '' or
        values['task_types'] == '' or
        values['task_name'] == '' or
        values['path'] == ''):
        return True
    return False

# checks if any values in the model opt dictionary are empty
def check_blank_options_model_opt(values):
    if (values['opt_queue'] == '' or
        values['opt_name'] == '' or
        values['opt_project'] == '' or
        values['task_name_for_opt'] == '' or 
        values['project_name_for_opt'] == ''):
        return True
    return False

# checks if any values in the param opt dictionary are empty
def check_blank_options_param_opt(values):
    if (values['opt_child_queue'] == '' or
        values['metric_to_optimize'] == '' or
        values['pool_period_min'] == '' or 
        values['max_number_of_concurrent_tasks'] == ''):
        return True
    if values['min_metric'] == False and values['max_metric'] == False:
        return True
    return False

# checks if any values default parameters are non numerical
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
        if value == '':
            continue
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
    for category in current_templates:
        for template in current_templates[category]:
            template_names.append(f'{category}: {template}')
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

# executes the configuration from the opt config
def exec_opt_config(opt_config):
    opt_name = opt_config['opt_name']
    opt_project = opt_config['opt_project']
    opt_queue = opt_config['opt_queue']
    create_populate = CreateAndPopulate(
        project_name=opt_project,
        task_name=opt_name,
        task_type=Task.TaskTypes.optimizer,
        script='optimizer.py',
    )
    create_populate.create_task()
    create_populate.task._set_runtime_properties({"_CLEARML_TASK": True})
    task_id = create_populate.get_id()
    Task.enqueue(create_populate.task, queue_name=opt_queue)
    return create_populate.task, task_id, opt_queue

# contructs the parameter optimization window layout from the given numeric and 
#   discrete parameters
def get_param_opt_layout(opt_config, numeric_params, discrete_params):
    numeric_params_layout = [[sg.Text('Parameter:', font='Ariel 14 bold')]]
    min_layout = [[sg.Text('Min:', font='Ariel 14 bold')]]
    max_layout = [[sg.Text('Max:', font='Ariel 14 bold')]]
    step_layout = [[sg.Text('Step:', font='Ariel 14 bold')]]
    for param in numeric_params:
        bool = numeric_params[param]
        if bool == int:
            bool_str = '(INT)'
        elif bool == float:
            bool_str = '(FLOAT)'
        numeric_params_layout.append(
                        [sg.Text(param), 
                         sg.Push(), 
                         sg.Text(bool_str)])
        min_layout.append(
            [sg.InputText(size=(5,1), key=f'{param}_min')])
        max_layout.append(
            [sg.InputText(size=(5,1), key=f'{param}_max')])
        step_layout.append(
            [sg.InputText(size=(5,1), key=f'{param}_step')])
        
    discrete_params_layout = [[sg.Text('Parameter:', font='Ariel 14 bold')]]
    discrete_values_layout = [[sg.Text('Values:', font='Ariel 14 bold')]]
    for param in discrete_params:
        discrete_params_layout.append([sg.Text(param)])
        discrete_values_layout.append(
            [sg.InputText(size=(20,1), key=f'{param}_values')])

    left_param_opt_layout = [
        [
            sg.Text('''
Input a min value, max value, and step size for each numeric 
parameter or leave blank if you do not wish to optimize.''', 
                    font='Ariel 12 bold')
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Column(numeric_params_layout),
            sg.Push(), 
            sg.Column(min_layout),
            sg.Push(), 
            sg.Column(max_layout),
            sg.Push(), 
            sg.Column(step_layout)
        ],
        [sg.VPush()]
    ]

    middle_param_opt_layout = [
        [
            sg.Text('''
Input values separated by commas for the following discrete 
parameters or leave blank if you do not wish to optimize.''', 
                    font='Ariel 12 bold'),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Column(discrete_params_layout),
            sg.Push(), 
            sg.Column(discrete_values_layout),
        ],
        [sg.VPush()]
    ]

    right_param_opt_layout = [
        [
            sg.Text('''
Default parameters for the optimization process. 
Required arguments are preceded by a red asterisk.''', 
                    font='Ariel 12 bold')
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Text('*', text_color='red'), 
            sg.Text('Please choose a queue to execute the child tasks')],
        [sg.OptionMenu([[]], key='opt_child_queue')],
        [sg.Text()],
        [
            sg.Text('*', text_color='red'),
            sg.Text('Metric to Optimize:'),
            sg.Push(), 
            sg.OptionMenu([[]], key='metric_to_optimize', size=(25,1))
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
            sg.InputText('', size=(5,1), key='max_number_of_concurrent_tasks')
        ],
        [
            sg.Text('Number of top tasks to save:'), 
            sg.Push(),
            sg.InputText('', size=(5,1), key='save_top_k_tasks_only')
        ],
        [
            sg.Text('Time limit per job in minutes:'),
            sg.Push(), 
            sg.InputText('', size=(5,1), key='time_limit_per_job')
        ],
        [
            sg.Text('*', text_color='red'),
            sg.Text('Time interval to check on the experiments in minutes:'),
            sg.Push(), 
            sg.InputText('', size=(5,1), key='pool_period_min')
        ],
        [
            sg.Text('Maximum number of jobs to launch for the optimization:'), 
            sg.Push(),
            sg.InputText('', size=(5,1), key='total_max_jobs')
        ],
        [
            sg.Text('Minimum number of iterations for an experiment:'), 
            sg.Push(),
            sg.InputText('', size=(5,1), key='min_iteration_per_job')
        ],
        [
            sg.Text('Maximum number of iterations for an experiment:'),
            sg.Push(), 
            sg.InputText('', size=(5,1), key='max_iteration_per_job')
        ],
        [
            sg.Text('Total time limit for the optimization in minutes:'),
            sg.Push(), 
            sg.InputText('', size=(5,1), key='total_time_limit')
        ],
        [sg.Checkbox('Save as template?', key='param_opt_save_as_template')],
        [sg.VPush()]
    ]

    param_opt_layout = [
        [
            sg.Push(), 
            sg.Text('Hyperparameter Optimization', font='Ariel 24 bold'),
            sg.Push()
        ],
        [
            sg.Push(),
            sg.Text('Optimizer Task Name:', font='Ariel 12 bold'),
            sg.Text(opt_config['opt_name']),
            sg.VerticalSeparator(),
            sg.Text('Optimizer Project:', font='Ariel 12 bold'),
            sg.Text(opt_config['opt_project']),
            sg.VerticalSeparator(),
            sg.Text('Model Task Name:', font='Ariel 12 bold'),
            sg.Text(opt_config['task_name_for_opt']),
            sg.VerticalSeparator(),
            sg.Text('Model Project:', font='Ariel 12 bold'),
            sg.Text(opt_config['project_name_for_opt']),
            sg.VerticalSeparator(),
            sg.Text('Optimizer Queue:', font='Ariel 12 bold'),
            sg.Text(opt_config['opt_queue']),
            sg.Push()
        ],
        [sg.HorizontalSeparator()],
        [
            sg.VerticalSeparator(),
            sg.Column(left_param_opt_layout, expand_y=True), 
            sg.VerticalSeparator(),
            sg.Column(middle_param_opt_layout, expand_y=True),
            sg.VerticalSeparator(),
            sg.Column(right_param_opt_layout, expand_y=True),
            sg.VerticalSeparator()
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Button('Confirm', key='param_opt_confirm'),
            sg.Button('Cancel', key='param_opt_cancel')
        ]
    ]

    return param_opt_layout