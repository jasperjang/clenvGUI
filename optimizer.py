
from clearml import Task
from clearml.automation.optuna import OptimizerOptuna
from clearml.automation import (
    HyperParameterOptimizer, 
    UniformIntegerParameterRange, 
    UniformParameterRange
)

def job_complete_callback(
        job_id,                 # type: str
        objective_value,        # type: float
        objective_iteration,    # type: int
        job_parameters,         # type: dict
        top_performance_job_id  # type: str
        ):  
        print('Job completed!', job_id, objective_value, objective_iteration, job_parameters)
        if job_id == top_performance_job_id:
            print('WOOT WOOT we broke the record! Objective reached {}'.format(objective_value))


def exec_opt_config(opt_config):
    opt_name = opt_config['opt_name']
    opt_project = opt_config['opt_project']
    task_name_for_opt = opt_config['task_name_for_opt']
    project_name_for_opt = opt_config['project_name_for_opt']
    queue = opt_config['queue']
    metric_to_optimize = opt_config['metric_to_optimize']
    min_metric = opt_config['min_metric']
    max_number_of_concurrent_tasks = opt_config['max_number_of_concurrent_tasks']
    save_top_k_tasks_only = opt_config['save_top_k_tasks_only']
    time_limit_per_job = opt_config['time_limit_per_job']
    pool_period_min = opt_config['pool_period_min']
    total_max_jobs = opt_config['total_max_jobs']
    min_iteration_per_job = opt_config['min_iteration_per_job']
    max_iteration_per_job = opt_config['max_iteration_per_job']
    total_time_limit = opt_config['total_time_limit']
    param_ranges = opt_config['param_ranges']

    hyper_parameters = []
    for param in param_ranges:
        params = param_ranges[param]
        if isinstance(params['min'], float):
            hyper_parameters.append(UniformParameterRange(
                param, 
                min_value=params['min'],
                max_value=params['max'],
                step_size=params['step'],
                include_max_value = True
            ))
        else:
            hyper_parameters.append(UniformIntegerParameterRange(
                param, 
                min_value=params['min'],
                max_value=params['max'],
                step_size=params['step'],
                include_max_value = True
            ))

    objective_metric_sign = ''
    if min_metric == True:
        objective_metric_sign = 'min'
    else:
        objective_metric_sign = 'max'

    task = Task.init(project_name=opt_project,
                 task_name=opt_name,
                 task_type=Task.TaskTypes.optimizer,
                 reuse_last_task_id=False)
    
    task.execute_remotely(queue_name=queue, clone=False, exit_process=True)

    task_for_opt_id = Task.get_task(project_name=project_name_for_opt, 
                                 task_name=task_name_for_opt).id

    an_optimizer = HyperParameterOptimizer(
        base_task_id=task_for_opt_id,
        hyper_parameters=hyper_parameters,
        objective_metric_title=metric_to_optimize,
        objective_metric_series=metric_to_optimize,
        objective_metric_sign=objective_metric_sign,
        max_number_of_concurrent_tasks=max_number_of_concurrent_tasks,
        optimizer_class=OptimizerOptuna,
        execution_queue=queue,
        save_top_k_tasks_only=save_top_k_tasks_only,
        time_limit_per_job=time_limit_per_job,
        pool_period_min=pool_period_min,
        total_max_jobs=total_max_jobs,
        min_iteration_per_job=min_iteration_per_job,
        max_iteration_per_job=max_iteration_per_job,
    )

    an_optimizer.set_report_period(pool_period_min)
    an_optimizer.start(job_complete_callback=job_complete_callback)
    an_optimizer.set_time_limit(in_minutes=total_time_limit)
    an_optimizer.wait()
    top_exp = an_optimizer.get_top_experiments(top_k=5)
    print([t.id for t in top_exp])
    an_optimizer.stop()
    
