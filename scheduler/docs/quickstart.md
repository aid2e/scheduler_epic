# Quick Start

This guide will help you get started with the Scheduler library quickly. We'll cover the basic workflow for setting up and running an optimization experiment.

## Basic Workflow

The typical workflow for using the Scheduler involves:

1. Defining your parameter space with Ax
2. Creating a runner for job execution
3. Setting up the scheduler with your objective function
4. Running the optimization

## Simple Example

Here's a minimal example that optimizes a simple function:

```python
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, JobLibRunner

# 1. Initialize Ax client and define parameter space
ax_client = AxClient()
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
    objectives={"objective": "minimize"},
)

# 2. Define your objective function
def objective_function(parameterization):
    x = parameterization["x"]
    y = parameterization["y"]
    return {"objective": (x - 0.5)**2 + (y - 0.5)**2}

# 3. Create a runner for local execution
runner = JobLibRunner(n_jobs=-1)  # Use all available cores

# 4. Create the scheduler
scheduler = AxScheduler(ax_client, runner)

# 5. Set the objective function
scheduler.set_objective_function(objective_function)

# 6. Run the optimization
best_params = scheduler.run_optimization(max_trials=10)
print("Best parameters:", best_params)
```

This example:
- Creates an experiment with two parameters (x and y)
- Defines a simple quadratic objective function
- Uses the JobLibRunner for local parallel execution
- Runs 10 trials to find the optimal parameter values

## Next Steps

For more advanced usage, check out:

- [Tutorial: Detector Optimization](tutorials/detector_optimization.md)
- [Tutorial: Using Slurm for Execution](tutorials/slurm_execution.md)
- [Tutorial: Container-Based Jobs](tutorials/container_jobs.md)
- [API Reference: AxScheduler](api/ax_scheduler.md)
- [API Reference: Runners](api/runners.md)
