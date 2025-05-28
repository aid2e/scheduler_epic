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

```python
# Create a script file: simulation_script.py
"""
#!/usr/bin/env python
import sys
import json
import numpy as np

# Parse input parameters
with open(sys.argv[1], 'r') as f:
    params = json.load(f)

# Extract parameters
field_strength = params['field_strength']
detector_length = params['detector_length']
detector_radius = params['detector_radius']

# Simulate detector performance
# Better resolution (lower is better) with higher field and larger size
resolution = 0.1 / field_strength * (1 + np.exp(-detector_length)) * (1 + np.exp(-detector_radius))

# Better acceptance (higher is better) with larger detector
acceptance = (1 - np.exp(-detector_length * detector_radius)) * 100

# Higher cost with larger detector and stronger field
cost = field_strength * 2 + detector_length * 10 + detector_radius * 15

# Write output
results = {
    "resolution": float(resolution),
    "acceptance": float(acceptance),
    "cost": float(cost)
}

with open(sys.argv[2], 'w') as f:
    json.dump(results, f)
"""
```

## Step 3: Initialize Ax Client and Define Parameter Space

```python
# Initialize Ax client
ax_client = AxClient()

# Define the parameter space
ax_client.create_experiment(
    name="epic_detector_optimization",
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

Here's the complete example:

```python
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, SlurmRunner
import os

def main():
    # Initialize Ax client
    ax_client = AxClient()
    
    # Define the parameter space
    ax_client.create_experiment(
        name="epic_detector_optimization",
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
    
    # Create output directory if it doesn't exist
    os.makedirs('./slurm_outputs', exist_ok=True)
    
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
    
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=20)
    
    # Print the results
    print("Best parameters:")
    print(best_params)
    
    # Get the best metrics
    best_metrics = ax_client.get_best_trial().values
    print("Best metrics:")
    print(best_metrics)
    
    # Save the experiment for later analysis
    scheduler.save_experiment("slurm_optimization_results.json")

if __name__ == "__main__":
    main()
```

## Monitoring Slurm Jobs

You can use standard Slurm commands to monitor your jobs:

```bash
# Check status of all your jobs
squeue -u $USER

# Check details of a specific job
scontrol show job <job_id>

# View the output file of a job
cat slurm-<job_id>.out
```

The Scheduler will also periodically check the status of your jobs and update the trial states accordingly.

## Handling Job Failures

If a Slurm job fails, the corresponding trial will be marked as failed. You can check the output files in the `job_output_dir` directory for error messages.

## Next Steps

- Try using containers with Slurm by checking out the [Container-Based Optimization](container_based_optimization.md) tutorial
- Explore batch trial submission with Slurm in the [Batch Trial Submission](batch_trial_submission.md) tutorial
- Learn how to save and load experiments in the [Experiment Persistence](experiment_persistence.md) tutorial
