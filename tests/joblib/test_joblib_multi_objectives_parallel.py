import logging

from ax.service.ax_client import AxClient, ObjectiveProperties
from scheduler import AxScheduler, JobLibRunner
from scheduler.utils.common import setup_logging
from scheduler.job.job import JobType
from scheduler.job.multi_steps_job import MultiStepsFunction


# Define your objective function
def objective_function1(x, y):
    return {"objective1": (x - 0.5) ** 2 + (y - 0.5) ** 2}


def objective_function2(x, y):
    return {"objective2": (x - 0.5) * 2 + (y - 0.5) * 2}


if __name__ == "__main__":
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
        objectives={
            "objective1": ObjectiveProperties(minimize=True),
            "objective2": ObjectiveProperties(minimize=True),
        },
    )

    logging.info("defining objectives")

    # Create a runner
    runner = JobLibRunner(n_jobs=-1)  # Use all available cores
    logging.info(f"created runner: {runner}")

    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    logging.info(f"created scheduler: {scheduler}")

    # Different steps can have dependencies
    # objectives in the same step are running in parallel.
    # For multiple objectives, the final result will use results.update(func_results),
    # which is different from global parameters.
    # If the first function returns {"a": 1}, the first function returns {"b": 2}, the
    # final result will be {"a": 1, "b": 2}
    objective_function = MultiStepsFunction(
        objective_funcs={
            "step1": {
                "objective1": {
                    "func": objective_function1,
                    "job_type": JobType.FUNCTION,
                    "runner": runner,
                },
                "objective2": {
                    "func": objective_function2,
                    "job_type": JobType.FUNCTION,
                    "runner": runner,
                },
            },
        },
        deps={},
    )

    # Set the objective function
    scheduler.set_objective_function(objective_function)

    logging.info("running optimization")
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=10)
    print("Best parameters:", best_params)
