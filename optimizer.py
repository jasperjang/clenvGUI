from clearml import Task
from clearml.automation.optuna import OptimizerOptuna
from clearml.automation import (
    DiscreteParameterRange, HyperParameterOptimizer, RandomSearch,
    UniformIntegerParameterRange, UniformParameterRange)

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

    task = Task.init(project_name=opt_project,
                 task_name=opt_name,
                 task_type=Task.TaskTypes.optimizer,
                 reuse_last_task_id=False)

    task.execute_remotely(queue_name=queue, clone=False, exit_process=True)

    task_for_opt_id = Task.get_task(project_name=project_name_for_opt, 
                                 task_name=task_name_for_opt).id

    an_optimizer = HyperParameterOptimizer(
        base_task_id=task_for_opt_id,
        hyper_parameters=[
            UniformIntegerParameterRange('General/layer_1', min_value=128, max_value=512, step_size=128),
            UniformIntegerParameterRange('General/layer_2', min_value=128, max_value=512, step_size=128),
            DiscreteParameterRange('General/batch_size', values=[96, 128, 160]),
            DiscreteParameterRange('General/epochs', values=[30]),
        ],
        objective_metric_title='epoch_accuracy',
        objective_metric_series='epoch_accuracy',
        objective_metric_sign='max',
        max_number_of_concurrent_tasks=2,
        optimizer_class=OptimizerOptuna,
        execution_queue=queue,
        # If specified only the top K performing Tasks will be kept, the others will be automatically archived
        save_top_k_tasks_only=None,  # 5,
        # Optional: Limit the execution time of a single experiment, in minutes.
        # (this is optional, and if using  OptimizerBOHB, it is ignored)
        time_limit_per_job=10.,
        # Check the experiments every 12 seconds is way too often, we should probably set it to 5 min,
        # assuming a single experiment is usually hours...
        pool_period_min=0.2,
        # set the maximum number of jobs to launch for the optimization, default (None) unlimited
        # If OptimizerBOHB is used, it defined the maximum budget in terms of full jobs
        # basically the cumulative number of iterations will not exceed total_max_jobs * max_iteration_per_job
        total_max_jobs=10,
        # set the minimum number of iterations for an experiment, before early stopping.
        # Does not apply for simple strategies such as RandomSearch or GridSearch
        min_iteration_per_job=10,
        # Set the maximum number of iterations for an experiment to execute
        # (This is optional, unless using OptimizerBOHB where this is a must)
        max_iteration_per_job=30,
    )

    # report every 12 seconds, this is way too often, but we are testing here 
    an_optimizer.set_report_period(0.2)
    # start the optimization process, callback function to be called every time an experiment is completed
    # this function returns immediately
    an_optimizer.start(job_complete_callback=job_complete_callback)
    # You can also use the line below instead to run all the optimizer tasks locally, without using queues or agent
    # an_optimizer.start_locally(job_complete_callback=job_complete_callback)
    # set the time limit for the optimization process (2 hours)
    an_optimizer.set_time_limit(in_minutes=120.0)
    # wait until process is done (notice we are controlling the optimization process in the background)
    an_optimizer.wait()
    # optimization is completed, print the top performing experiments id
    top_exp = an_optimizer.get_top_experiments(top_k=3)
    print([t.id for t in top_exp])
    # make sure background optimization stopped
    an_optimizer.stop()

opt_config = {
    'opt_name':'Test',
    'opt_project':'Hyper-Parameter Optimization',
    'task_name_for_opt':'Keras HP optimization base',
    'project_name_for_opt':'MNIST-test',
    'queue':'ml-universal-pip'
}
exec_opt_config(opt_config)