# Scheduler for AID2E

A Python library for scheduling and managing optimization trials for the ePIC EIC detector design using Ax, with support for multiple execution backends and job types.

## Features

- Direct integration with Ax for optimization
- Support for multiple job types:
  - Python functions
  - Shell/Python scripts
  - Containers (Docker/Singularity)
- Multiple execution backends:
  - JobLib (local parallel execution)
  - Slurm (cluster computing)
  - PanDA (distributed computing)
- Trial and job state monitoring
- Synchronous or asynchronous execution
- Batch trial submission for parallel exploration
- Experiment saving and loading

## Installation

```bash
# Basic installation
pip install -e .

# With Slurm support
pip install -e .[slurm]

# With PanDA support
pip install -e .[panda]
```

## Usage

### Basic Function-based Optimization

```python
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, JobLibRunner

# Initialize Ax client
ax_client = AxClient()

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
    objectives={"objective": "minimize"},
)

# Define your objective function
def objective_function(parameterization):
    x = parameterization["x"]
    y = parameterization["y"]
    return {"objective": (x - 0.5)**2 + (y - 0.5)**2}

# Create a runner
runner = JobLibRunner(n_jobs=-1)  # Use all available cores

# Create the scheduler
scheduler = AxScheduler(ax_client, runner)

# Set the objective function
scheduler.set_objective_function(objective_function)

# Run the optimization
best_params = scheduler.run_optimization(max_trials=10)
print("Best parameters:", best_params)
```

### Script-based Optimization

```python
from scheduler import AxScheduler, JobLibRunner

# Create a scheduler
scheduler = AxScheduler(ax_client, runner)

# Use a script as the objective function
scheduler.set_script_objective("./my_simulation_script.py")

# Run the optimization
best_params = scheduler.run_optimization(max_trials=10)
```

### Container-based Optimization

```python
from scheduler import AxScheduler, SlurmRunner

# Create a Slurm runner for container execution
runner = SlurmRunner(
    partition="compute",
    time_limit="01:00:00",
    memory="4G",
    cpus_per_task=4,
    config={
        'modules': ['singularity']
    }
)

# Create the scheduler
scheduler = AxScheduler(ax_client, runner)

# Use a container as the objective function
scheduler.set_container_objective(
    container_image="my/simulation:latest",
    container_command="python /app/simulate.py"
)

# Run the optimization
best_params = scheduler.run_optimization(max_trials=10)
```

### Batch Trial Submission

```python
# Create a batch of trials to run in parallel
with scheduler.batch_trial_context() as batch:
    # Add trials with specific parameter values
    batch.add_trial({"x": 0.1, "y": 0.2})
    batch.add_trial({"x": 0.3, "y": 0.4})
    batch.add_trial({"x": 0.5, "y": 0.6})
    
    # The trials will be run when exiting the context
```

### Saving and Loading Experiments

```python
# Save the experiment to a file
scheduler.save_experiment("my_experiment.json")

# Load the experiment from a file
new_scheduler = AxScheduler(None, runner)
new_scheduler.load_experiment("my_experiment.json")
```

## Advanced Configuration

The scheduler and runners support various configuration options:

```python
# Configure the scheduler
scheduler = AxScheduler(
    ax_client, 
    runner,
    config={
        'monitoring_interval': 10,  # Seconds between status checks
        'job_output_dir': './outputs',  # Directory for job outputs
        'synchronous': True,  # Run trials synchronously
        'cleanup_after_completion': True  # Clean up files after completion
    }
)

# Configure the JobLib runner
joblib_runner = JobLibRunner(
    n_jobs=-1,
    backend='loky',
    config={
        'container_engine': 'docker',  # or 'singularity'
        'tmp_dir': './tmp'  # Directory for temporary files
    }
)

# Configure the Slurm runner
slurm_runner = SlurmRunner(
    partition="compute",
    time_limit="01:00:00",
    memory="4G",
    cpus_per_task=4,
    config={
        'modules': ['python', 'singularity'],  # Modules to load
        'sbatch_options': {
            'account': 'my-project',
            'mail-user': 'user@example.com',
            'mail-type': 'END,FAIL'
        }
    }
)
```

## Examples

See the `examples` directory for more advanced usage examples:

- `detector_optimization.py` - Basic function-based optimization
- `enhanced_detector_optimization.py` - Advanced function-based optimization
- `slurm_optimization.py` - Optimization using Slurm for compute
- `container_detector_optimization.py` - Container-based optimization

## Documentation

Comprehensive documentation is available in the `docs/` directory. You can also access the hosted documentation at:

https://aid2e.github.io/scheduler_epic/installation/

The documentation includes:
- Installation instructions
- Quick start guide
- Detailed tutorials
- API reference
- Architecture overview

To build the documentation locally, install MkDocs and run:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Then visit http://127.0.0.1:8000/ in your browser.

## License

[MIT License](LICENSE)