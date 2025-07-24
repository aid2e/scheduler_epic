import logging
import os

# Define your objective function at module level (like PanDAiDDS)
def slurm_objective_function(x, y):
    """Objective function that will be serialized and executed on SLURM."""
    result = (x - 0.5) ** 2 + (y - 0.5) ** 2
    return {"objective": result}

# Similar to PanDAiDDS pattern - avoid executing main logic during import
if __name__ == "__main__":
    # Import scheduler components here (like PanDAiDDS example)
    from ax.service.ax_client import AxClient, ObjectiveProperties
    from scheduler import AxScheduler
    from scheduler.runners.slurm_runner import SlurmRunner
    from scheduler.utils.common import setup_logging

    setup_logging(log_level="debug")

    logging.debug("Setting up Ax client")
    ax_client = AxClient()

    logging.info("Creating experiment")
    ax_client.create_experiment(
        name="slurm_experiment",
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

    logging.info("Creating SlurmRunner")
    runner = SlurmRunner(
        name="slurm_test_runner",
        partition="batch",
        time_limit="00:10:00",
        memory="1G",
        cpus_per_task=1,
        config={
            "job_dir": os.path.join(os.getcwd(), "slurm_jobs_scheduler_test")
        },
    )

    logging.info("Initializing AxScheduler with SlurmRunner")
    scheduler = AxScheduler(ax_client, runner)

    logging.info("Setting objective function")
    scheduler.set_objective_function(slurm_objective_function)

    logging.info("Running optimization on SLURM")
    best_params = scheduler.run_optimization(max_trials=5)

    print("Best parameters:", best_params)