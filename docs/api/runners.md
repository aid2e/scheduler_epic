# Runners

Runners are responsible for executing jobs on different computing backends.

## Classes

### [BaseRunner](baserunner.md)

Abstract base class for job runners.

### [JobLibRunner](joblibrunner.md)

A runner that uses joblib for parallel execution.

### [SlurmRunner](slurmrunner.md)

A runner that submits jobs to a Slurm cluster.

## Class Hierarchy

```
BaseRunner
├── JobLibRunner
└── SlurmRunner
```

## Usage Examples

```python
# Using JobLibRunner for local parallel execution
from scheduler import AxScheduler, JobLibRunner
from ax.service.ax_client import AxClient

runner = JobLibRunner(n_jobs=4)  # Use 4 parallel processes
scheduler = AxScheduler(ax_client, runner)

# Using SlurmRunner for cluster execution
from scheduler import SlurmRunner

runner = SlurmRunner(
    partition='compute',
    time='1:00:00',
    memory='4G'
)
scheduler = AxScheduler(ax_client, runner)
```

