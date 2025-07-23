import argparse
import logging

from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.modelbridge.registry import Generators
from ax.modelbridge.generation_strategy import GenerationStrategy, GenerationStep
from scheduler import AxScheduler, JobLibRunner
from scheduler.utils.common import setup_logging
from scheduler.job.job import JobType
from scheduler.job.multi_steps_job import MultiStepsFunction


# DTLZ2: m objectives, d-dimensional input
def dtlz2_torch(X, m=2):
    """
    X: torch.Tensor of shape (batch_size, d)
    Returns: torch.Tensor of shape (batch_size, m)
    """
    import math
    import torch

    X = torch.tensor(X, dtype=torch.float32)
    batch_size, d = X.shape

    # g is based on the last k variables (k = d - m + 1)
    k = d - m + 1
    g = torch.sum((X[:, -k:] - 0.5) ** 2, dim=1)

    f = []
    for i in range(m):
        prod = torch.ones(batch_size)
        for j in range(m - i - 1):
            prod *= torch.cos(0.5 * math.pi * X[:, j])
        if i != 0:
            prod *= torch.sin(0.5 * math.pi * X[:, m - i - 1])
        else:
            prod *= 1  # purely for clarity; already set to 1 above
        f_i = (1 + g) * prod
        f.append(f_i)

    return torch.stack(f, dim=1)


def dtlz2(X, m=2):
    """
    DTLZ2 function using NumPy.

    Parameters:
    - X: np.ndarray of shape (n_points, d), decision variables in [0,1]
    - m: int, number of objectives

    Returns:
    - f: np.ndarray of shape (n_points, m), objective values
    """
    import numpy as np

    X = np.asarray(X, dtype=np.float64)
    n_points, d = X.shape
    k = d - m + 1
    g = np.sum((X[:, -k:] - 0.5) ** 2, axis=1)

    f = np.ones((n_points, m)) * (1 + g[:, np.newaxis])

    for i in range(m):
        for j in range(m - i - 1):
            f[:, i] *= np.cos(0.5 * np.pi * X[:, j])
        if i > 0:
            f[:, i] *= np.sin(0.5 * np.pi * X[:, m - i - 1])

    return f


def objective_function_torch(num_objs=2, **params):
    import torch

    x = [params[f"x{i}"] for i in range(len(params))]
    x_tensor = torch.tensor([x], dtype=torch.float32)
    f = dtlz2(x_tensor, m=num_objs)[0]
    return {f"f{i + 1}": (f[i].item(), 0.0) for i in range(num_objs)}


def objective_function(num_objs=2, **params):
    import numpy as np

    x = [params[f"x{i}"] for i in range(len(params))]
    x_array = np.array([x])  # shape: (1, d)
    f = dtlz2(x_array, m=num_objs)[0]
    return {f"f{i + 1}": (float(f[i]), 0.0) for i in range(num_objs)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--objectives", type=int, default=2, help="Number of objectives (e.g., 2)")
    parser.add_argument("--trials", type=int, default=20, help="Number of trials")
    parser.add_argument("--parameters", type=int, default=6, help="Number of parameters")
    args = parser.parse_args()

    num_obj = args.objectives
    num_trials = args.trials
    num_parameters = args.parameters

    setup_logging(log_level="debug")
    logging.info(f"num objectives: {num_obj}, num trials: {num_trials}, num parameters: {num_parameters}")

    logging.debug("setup ax client")

    generation_strategy = GenerationStrategy(
        steps=[
            GenerationStep(model=Generators.SOBOL, num_trials=5),
            GenerationStep(model=Generators.BOTORCH_MODULAR, num_trials=-1),
        ]
    )

    # Initialize Ax client
    ax_client = AxClient(generation_strategy=generation_strategy)

    logging.info("Creating experiment")

    # Define search space
    parameters = [{"name": f"x{i}", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"} for i in range(num_parameters)]

    # Define objectives and thresholds
    objectives = {f"f{i + 1}": ObjectiveProperties(minimize=True) for i in range(num_obj)}
    thresholds = [{"metric_name": f"f{i + 1}", "bound": "1.0", "op": "<="} for i in range(num_obj)]

    global_parameters = [{"num_objs": num_obj}]

    # Define your parameter space
    ax_client.create_experiment(
        name="my_experiment",
        parameters=parameters,
        objectives=objectives,
        # objective_thresholds=thresholds,
    )

    logging.info("defining objectives")

    # Create a runner
    runner = JobLibRunner(n_jobs=-1)  # Use all available cores
    logging.info(f"created runner: {runner}")

    objective_function_multi = MultiStepsFunction(
        objective_funcs={
            "one_step": {
                "func": objective_function,
                "job_type": JobType.FUNCTION,
                "runner": runner
            },
        },
        deps=None,
        global_parameters=global_parameters,
        global_parameters_steps=["one_step"],
    )

    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    logging.info(f"created scheduler: {scheduler}")

    # Set the objective function
    # scheduler.set_objective_function(objective_function)
    scheduler.set_objective_function(objective_function_multi)

    logging.info("running optimization")
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=10)
    print("Best parameters:", best_params)
