import logging


# Define your objective function
def objective_function(x, y):
    return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2}
# This file will be imported to load the objective function at remote sites in PanDA
# to avoid excuting the whole file, __name__ == "__main__" must be used.
# There is another way to only ship the codes of the objective function to remote sites.
# However, if this objective function calls some other functions, this way of only shipping
# the function codes will not work.
if __name__ == "__main__":
    # move imports here
    # so the remote execution will not import these libraries
    from ax.service.ax_client import AxClient, ObjectiveProperties
    from scheduler import AxScheduler, SlurmRunner
    from scheduler.utils.common import setup_logging

    setup_logging(log_level="debug")

    logging.debug("setup ax client")
    # Initialize Ax client
    ax_client = AxClient()

    logging.info("Creating experiment")

    # Define your parameter space
    parameters = []
    ax_client.create_experiment(
        name="my_experiment",
        parameters=[
            {
                "name": "x",
                "type": "range",
                "bounds": [0.0, 1.0],
                "value_type": "float",
            },
            {
                "name": "y",
                "type": "range",
                "bounds": [0.0, 1.0],
                "value_type": "float",
            },
        ],
        objectives={"objective": ObjectiveProperties(minimize=True)},
    )

    logging.info("defining objectives")

    # Slurm attributes
    init_env = [
        "module load miniforge3/24.9.2-0", 
        "conda activate env_AID2EHol"
    ]
    
    slurm_attrs = {
        "slurm_template": "/sciclone/home/ksuresh/scr10/scheduler_epic/tests/slurm/slurm.template",
        "init_env": init_env
    }

    # Create a runner
    runner = SlurmRunner(**slurm_attrs)
    logging.info(f"created runner: {runner}")

    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    logging.info(f"created scheduler: {scheduler}")

    # Set the objective function
    scheduler.set_objective_function(objective_function)

    logging.info("running optimization")
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=10)
    print("Best parameters:", best_params)
