# Tutorial: Using Slurm for Execution

This tutorial demonstrates how to use the Scheduler library with Slurm for running optimization trials on a cluster. Using Slurm allows you to scale up your optimization by distributing trials across multiple compute nodes.

## Prerequisites

- Scheduler library installed with Slurm support (`pip install -e .[slurm]`)
- Access to a Slurm cluster
- Basic understanding of Slurm concepts (partitions, job submission, etc.)

## Step 1: Import Required Libraries

```python
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, SlurmRunner
```

## Step 2: Define Your Objective Function

For this example, we'll use a script-based objective instead of a Python function, since this is more common in HPC environments:

A toy function goes here

## Step 3: Initialize Ax Client and Define Parameter Space

```python
# Initialize Ax client
ax_client = AxClient()

# Define the parameter space
ax_client.create_experiment(
    name="slurm_optimization",
    parameters=[
        {
            "name": "field_strength",
            "type": "range",
            "bounds": [1.0, 3.0],
            "value_type": "float",
        },
        {
            "name": "detector_length",
            "type": "range",
            "bounds": [4.0, 8.0],
            "value_type": "float",
        },
        {
            "name": "detector_radius",
            "type": "range",
            "bounds": [1.0, 3.0],
            "value_type": "float",
        },
    ],
    objectives={
        "resolution": "minimize",
        "acceptance": "maximize",
    },
    outcome_constraints=["cost <= 100.0"],
)
```

## Step 4: Create a Slurm Runner

```python
# Create a runner for Slurm execution
runner = SlurmRunner(
    partition="compute",       # Specify your partition
    time_limit="00:30:00",     # 30 minutes per job
    memory="4G",               # 4GB of memory per job
    cpus_per_task=4,           # 4 CPUs per task
    config={
        'modules': ['python/3.9'],  # Modules to load
        'sbatch_options': {
            'account': 'eic-project',       # Your account/allocation
            'mail-user': 'user@example.com',  # Email for notifications
            'mail-type': 'END,FAIL'           # When to send notifications
        }
    }
)
```

## Step 5: Create the Scheduler and Set Script Objective

```python
# Create the scheduler
scheduler = AxScheduler(
    ax_client, 
    runner,
    config={
        'job_output_dir': './slurm_outputs',  # Directory for job outputs
        'synchronous': False,                  # Run trials asynchronously
        'monitoring_interval': 30              # Check status every 30 seconds
    }
)

# Set the script objective
scheduler.set_script_objective(
    script_path="./simulation_script.py",
    script_options={
        'interpreter': 'python',  # Use Python to run the script
        'timeout': 1200           # Timeout in seconds (20 minutes)
    }
)
```

## Step 6: Run the Optimization

```python
# Run the optimization
best_params = scheduler.run_optimization(max_trials=20)

# Print the results
print("Best parameters:")
print(best_params)

# Get the best metrics
best_metrics = ax_client.get_best_trial().values
print("Best metrics:")
print(best_metrics)
```

## Complete Example

Write a complete example

## Next Steps

- Try using containers with Slurm by checking out the [Container-Based Optimization](container_based_optimization.md) tutorial
- Explore batch trial submission with Slurm in the [Batch Trial Submission](batch_trial_submission.md) tutorial
- Learn how to save and load experiments in the [Experiment Persistence](experiment_persistence.md) tutorial
