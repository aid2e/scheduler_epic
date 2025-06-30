import logging

from ax.service.ax_client import AxClient, ObjectiveProperties
from scheduler import AxScheduler, JobLibRunner
from scheduler.utils.common import setup_logging


# Define your objective function
def objective_function1(parameterization):
    x = parameterization["x"]
    y = parameterization["y"]
    return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2}


def objective_function(x, y):
    return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2}


if __name__ == "main":
    setup_logging(log_level="debug")

    logging.debug("setup ax client")
    # Initialize Ax client
    ax_client = AxClient()

    logging.info("Creating experiment")

    # Define your parameter space
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

    # Create a runner
    runner = JobLibRunner(n_jobs=-1)  # Use all available cores
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
