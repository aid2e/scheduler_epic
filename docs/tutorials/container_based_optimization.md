# Tutorial: Container-Based Optimization

This tutorial demonstrates how to use the Scheduler library with containers (Docker or Singularity) for optimization tasks. Containers provide consistent execution environments and can help ensure reproducibility of results.

## Prerequisites

- Scheduler library installed
- Docker or Singularity installed on your system
- Basic understanding of containers

## Step 1: Prepare Your Container

First, you need a container image that includes your simulation or analysis code. Here's an example Dockerfile:

```dockerfile
# Use a suitable base image
FROM python:3.9-slim

# Install dependencies
RUN pip install numpy scipy pandas matplotlib

# Copy your simulation code
COPY simulation.py /app/simulation.py

# Set the working directory
WORKDIR /app

# The container will be run with the command passed via the scheduler
```

Build the container image:

```bash
docker build -t epic-simulation:latest .
```

## Step 2: Import Required Libraries

```python
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, JobLibRunner
```

## Step 3: Initialize Ax Client and Define Parameter Space

```python
# Initialize Ax client
ax_client = AxClient()

# Define the parameter space
ax_client.create_experiment(
    name="container_detector_optimization",
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

## Step 4: Create a Runner with Container Support

```python
# Create a runner with container support
runner = JobLibRunner(
    n_jobs=4,  # Use 4 cores
    config={
        'container_engine': 'docker',  # or 'singularity'
        'tmp_dir': './container_tmp'   # Directory for temporary files
    }
)
```

## Step 5: Create the Scheduler and Set Container Objective

```python
# Create the scheduler
scheduler = AxScheduler(
    ax_client, 
    runner,
    config={
        'job_output_dir': './container_outputs',  # Directory for job outputs
        'monitoring_interval': 10                 # Check status every 10 seconds
    }
)

# Set the container objective
scheduler.set_container_objective(
    container_image="epic-simulation:latest",
    container_command="python simulation.py {params_file} {output_file}",
    container_options={
        'volumes': {
            './data': '/app/data',  # Mount local data directory
        },
        'env_vars': {
            'DEBUG': '1'
        }
    }
)
```

The `{params_file}` and `{output_file}` placeholders will be automatically replaced with the paths to the parameter and output files.

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

Writing the complete example now.

## Next Steps

- Try combining containers with Slurm execution for scalable, reproducible optimization
- Explore saving and loading container-based experiments in the [Experiment Persistence](experiment_persistence.md) tutorial
- Learn about batch trial submission in the [Batch Trial Submission](batch_trial_submission.md) tutorial
