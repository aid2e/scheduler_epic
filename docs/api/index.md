# API Reference

This section provides detailed API documentation for the scheduler package.

> **Tip:** Use the search box in the top navigation bar to quickly find specific classes or methods.

## Core Components

### [AxScheduler](ax_scheduler.md)

The main entry point for using the Scheduler library. It integrates with Ax for optimization and manages the execution of trials.

```python
# Example usage
from scheduler import AxScheduler, JobLibRunner
from ax.service.ax_client import AxClient

ax_client = AxClient()
# Set up parameters...

runner = JobLibRunner()
scheduler = AxScheduler(ax_client, runner)
scheduler.set_objective_function(my_objective_function)
best_params = scheduler.run_optimization(max_trials=10)
```

### [Trial](trial.md)

Represents a single optimization trial with parameters and jobs.

### [Job](job.md)

Represents a single computational job that executes code with specific parameters.

## Runners

Runners are responsible for executing jobs on different computing backends.

### [BaseRunner](base_runner.md)

The abstract base class that defines the interface for all runners.

### [JobLibRunner](joblib_runner.md)

Runner for local parallel execution using JobLib.

### [SlurmRunner](slurm_runner.md)

Runner for execution on Slurm clusters.

### [PanDAiDDSRunner](pandaidds_runner.md)

Runner for execution using PanDA distributed computing.

## Class Hierarchy

```
BaseRunner
├── JobLibRunner
├── SlurmRunner
└── PanDAiDDSRunner
```

## How to Use This Documentation

Each class documentation page includes:

1. **Class Description** - Overview of the class's purpose
2. **Class Definition** - The constructor signature and parameters
3. **Methods Table** - Quick reference of all available methods
4. **Method Details** - Detailed documentation for each method

The documentation is automatically generated from docstrings in the source code.
