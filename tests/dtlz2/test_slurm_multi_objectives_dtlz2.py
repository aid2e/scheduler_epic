import argparse
import logging
from pathlib import Path

# DTLZ2: m objectives, d-dimensional input

def objective_function_torch(num_objs=2, **params):
    import torch
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

        f_vals = f / np.linalg.norm(f, axis=1, keepdims=True)
        return f_vals


    x = [params[f"x{i}"] for i in range(len(params))]
    x_tensor = torch.tensor([x], dtype=torch.float32)
    f = dtlz2(x_tensor, m=num_objs)[0]
    return {f"f{i + 1}": (f[i].item(), 0.0) for i in range(num_objs)}



if __name__ == "__main__":
    from ax.service.ax_client import AxClient, ObjectiveProperties
    from ax.modelbridge.registry import Generators
    from ax.modelbridge.generation_strategy import GenerationStrategy, GenerationStep
    from scheduler import AxScheduler, SlurmRunner
    from scheduler.utils.common import setup_logging
    from scheduler.job.job import JobType
    from scheduler.job.multi_steps_job import MultiStepsFunction

    parser = argparse.ArgumentParser()
    parser.add_argument("--objectives", type=int, default=2, help="Number of objectives (e.g., 2)")
    parser.add_argument("--trials", type=int, default=20, help="Number of trials")
    parser.add_argument("--parameters", type=int, default=6, help="Number of parameters")
    parser.add_argument("--name", type=str, default="dtlz2", help="Name for the optimization")
    parser.add_argument("--slurm_template", type=str, help="Path to the SLURM job template")

    args = parser.parse_args()

    num_obj = args.objectives
    num_trials = args.trials
    num_parameters = args.parameters
    name = args.name
    slurm_template = Path(args.slurm_template)

    setup_logging(log_level="debug")
    logging.info(f"num objectives: {num_obj}, num trials: {num_trials}, num parameters: {num_parameters}")

    logging.debug("setup ax client")

    generation_strategy = GenerationStrategy(
        steps=[
            GenerationStep(model=Generators.SOBOL, num_trials=5, min_trials_observed=3, max_parallelism=5),
            GenerationStep(model=Generators.BOTORCH_MODULAR, num_trials=-1, max_parallelism=5),
        ]
    )
    # LEGACY_BOTORCH
  
    # Initialize Ax client
    ax_client = AxClient(generation_strategy=generation_strategy)

    logging.info("Creating experiment")

    # Define search space
    parameters = [{"name": f"x{i}", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"} for i in range(num_parameters)]

    # Define objectives and thresholds
    objectives = {f"f{i + 1}": ObjectiveProperties(minimize=True, threshold=1.1) for i in range(num_obj)}
    # thresholds = [{"metric_name": f"f{i + 1}", "bound": "1.0", "op": "<="} for i in range(num_obj)]

    global_parameters = [{"num_objs": num_obj}]

    # Define your parameter space
    ax_client.create_experiment(
        name=name,
        parameters=parameters,
        objectives=objectives,
        # objective_thresholds=thresholds,
    )

    # Slurm attributes
    init_env = [
        "module load miniforge3/24.9.2-0", 
        "conda activate env_AID2EHol"
    ]

    slurm_attrs = {
        "slurm_template": slurm_template,
        "init_env": init_env
    }

    # Create a runner
    runner = SlurmRunner(**slurm_attrs)
    logging.info(f"created runner: {runner}")

    logging.info("defining objectives")

    # Create a runner
    # runner = JobLibRunner(n_jobs=-1)  # Use all available cores
    # logging.info(f"created runner: {runner}")

    objective_function_multi = MultiStepsFunction(
        objective_funcs={
            "one_step": {
                "func": objective_function_torch,
                "job_type": JobType.FUNCTION,
                "runner": runner
            },
        },
        deps=None,
        global_parameters=global_parameters,
        global_parameters_steps=["one_step"],
    )

    config = {
        "max_concurrent_trials": 5,
        "early_stopping_threshold": None,
        "early_stopping_begin_at": 0,
        "restart_from_checkpoint": True,
        "work_dir": f"/sciclone/home/ksuresh/scr10/ax-outputs/dtlz2-{num_obj}-{num_trials}",
        "job_output_dir" : f"/sciclone/home/ksuresh/scr10/ax-jobs/dtlz2-{num_obj}-{num_trials}/jobs",
        "checkpoint_name": None,    # will use experiment name
    }

    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner, config=config)
    logging.info(f"created scheduler: {scheduler}")

    # Set the objective function
    # scheduler.set_objective_function(objective_function)
    scheduler.set_objective_function(objective_function_multi)

    logging.info("running optimization")
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=num_trials)
    print("Best parameters:", best_params)
