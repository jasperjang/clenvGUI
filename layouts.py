import PySimpleGUI as sg

task_types = [
    "training",
    "testing",
    "inference",
    "data_processing",
    "application",
    "monitor",
    "controller",
    "optimizer",
    "service",
    "qc",
    "other"
]

main_layout = [
    [
        sg.Push(),
        sg.Button('   Remote Execution   ', font='Ariel 18 bold', key='run_template_new'),
        sg.Push(),
        sg.Button('  Model Optimization  ', font='Ariel 18 bold', key='model_opt'),
        sg.Push()
    ],
    [sg.Text()],
    [sg.Text('Select a template to run or delete:')],
    [sg.Listbox(['No templates created'], key='template_chosen', size=(70,9))],
    [
        sg.Button('Run Template', key='run_template_template'),
        sg.Button('Delete Template', key='run_template_delete'),
    ],
    [sg.Text('')],
    [sg.Text('')],
    [sg.Text('')],
    [sg.Text('')],
    [
        sg.Button('Profile Configuration', key='config'), 
        sg.Push(), 
        sg.Button('QUIT', key='quit')
    ]
]

exec_layout = [
    [sg.Text('Choose a queue to execute the task:')],
    [sg.OptionMenu([[]], key='queue_list')],
    [sg.Text('')],
    [sg.Text('Choose a task type:')],
    [sg.OptionMenu(task_types, key='task_types')],
    [sg.Text('')],
    [sg.Text('Enter a task name:')],
    [sg.InputText('', key='task_name')],
    [sg.Text('')],
    [sg.Text('Enter the script path:')],
    [sg.InputText('/', key='path')],
    [sg.Text('')],
    [sg.Text('Tags separated by commas (optional):')],
    [sg.InputText('', key='tags')],
    [sg.Checkbox('Save as template?', key='save_as_template')],
    [
        sg.Button('Confirm', key='exec_confirm'), 
        sg.Button('Back', key='exec_back')
    ]
]

exec_complete_layout = [
    [sg.Text(f"New task created id='{'task_id'}'", key='exec_complete_text1')],
    [sg.Text(f"Execution on queue {'queue'}", key='exec_complete_text2')],
    [sg.Text("Execution log at:")],
    [sg.Button('Navigate to project on clearML', key='exec_complete_URL')],
    [sg.Button('Back', key='exec_complete_back')]
]

config_layout = [
    [sg.Text('Profile Configuration Options:')],
    [sg.OptionMenu(['Checkout a Profile',
                    'Create a Profile',
                    'Delete a Profile',
                    'List of Profiles',
                    'Rename a Profile',
                    'Configure API Path'], key='config_options')],
    [
        sg.Button('Confirm', key='config_confirm'), 
        sg.Button('Back', key='config_back')
    ]
]

config_checkout_layout = [
    [sg.Text('Select a profile to checkout:')],
    [sg.Text(f'Active Profile: {"active_profile"}', key='checkout_active_profile')],
    [sg.OptionMenu([{}], key='checkout_non_active_profiles')],
    [
        sg.Button('Confirm', key='config_checkout_confirm'), 
        sg.Button('Back', key='config_checkout_back')
    ]
]

config_create_layout = [
    [sg.Text('Enter a new profile name:')],
    [sg.InputText('', key='new_profile_name')],
    [
        sg.Button('Confirm', key='config_create_confirm'),
        sg.Button('Back', key='config_create_back')
    ]
]

config_delete_layout = [
    [sg.Text('Select a profile to delete:')],
    [sg.OptionMenu([{}], key='delete_non_active_profiles')],
    [
        sg.Button('Confirm', key='config_delete_confirm'),
        sg.Button('Back', key='config_delete_back')
    ]
]

config_list_layout = [
    [sg.Text('List of profiles:')],
    [sg.Text('profile_string', key='profile_list')],
    [sg.Button('Back', key='config_list_back')]
]

config_rename_layout = [
    [sg.Text('Select a profile to rename:')],
    [sg.OptionMenu([[]], key='profile_list_menu')],
    [sg.Text('')],
    [sg.Text('Enter a new name:')],
    [sg.InputText('', key='profile_rename')],
    [
        sg.Button('Confirm', key='config_rename_confirm'),
        sg.Button('Back', key='config_rename_back')
    ]
]

config_configure_layout = [
    [sg.Text('Select a profile to reconfigure:')],
    [sg.OptionMenu([[]], key='profile_to_config')],
    [sg.Text('')],
    [sg.Text('Enter a multiline configuration below:')],
    [sg.Text('''
This can be found by navigating to the clearML website, 
clicking the button in the top right corner, then 
settings > workspace > create new credentials
             ''')],
    [sg.Multiline('', key='multiline_config', size=(60,8))],
    [
        sg.Button('Confirm', key='config_configure_confirm'),
        sg.Button('Back', key='config_configure_back')
    ]
]

model_opt_layout = [
    [sg.Text('Choose a queue to host the optimization task:')],
    [sg.OptionMenu([[]], key='opt_queue')],
    [sg.Text()],
    [sg.Text('Enter a task name for the optimizer:')],
    [sg.InputText('', key='opt_name')],
    [sg.Text('')],
    [sg.Text('Enter project name for the optimizer:')],
    [sg.InputText('', key='opt_project')],
    [sg.Text('')],
    [sg.Text('Enter the name of the task you want to optimize:')],
    [sg.InputText('', key='task_name_for_opt')],
    [sg.Text('')],
    [sg.Text('Enter the name of the project where the task is located:')],
    [sg.InputText('', key='project_name_for_opt')],
    [sg.Text('')],
    [
        sg.Button('Confirm', key='model_opt_confirm'), 
        sg.Button('Back', key='model_opt_back')
    ]
]

model_opt_complete_layout = [
    [sg.Text(f"New task created id='{'task_id'}'", key='model_opt_complete_text1')],
    [sg.Text(f"Execution on queue {'queue'}", key='model_opt_complete_text2')],
    [sg.Text("Execution log at:")],
    [sg.Button('Navigate to project on clearML', key='model_opt_complete_URL')],
    [sg.Button('Back', key='model_opt_complete_back')]
]