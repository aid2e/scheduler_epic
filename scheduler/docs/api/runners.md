# Runners

Runners are responsible for executing jobs on different systems. The Scheduler library provides several runners for different execution environments.

## BaseRunner

The `BaseRunner` is an abstract base class that defines the interface for all runners.

```python
class BaseRunner(ABC):
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize a new runner.
        
        Args:
            config: Configuration for the runner
        """
```

### Key Methods

```python
@abstractmethod
def run_job(self, job: Job) -> None:
    """
    Run a job.
    
    Args:
        job: The job to run
    """
```

```python
@abstractmethod
def check_job_status(self, job: Job) -> None:
    """
    Check the status of a job and update its state.
    
    Args:
        job: The job to check
    """
```

```python
@abstractmethod
def cancel_job(self, job: Job) -> None:
    """
    Cancel a job.
    
    Args:
        job: The job to cancel
    """
```

## JobLibRunner

The `JobLibRunner` executes jobs locally using joblib for parallelization.

```python
class JobLibRunner(BaseRunner):
    def __init__(self, n_jobs: int = -1, backend: str = 'loky', config: Dict[str, Any] = None):
        """
        Initialize a new JobLibRunner.
        
        Args:
            n_jobs: Number of parallel jobs (-1 for all cores)
            backend: Joblib backend ('loky', 'threading', or 'multiprocessing')
            config: Additional configuration
        """
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `container_engine` | str | None | Container engine to use ('docker' or 'singularity') |
| `tmp_dir` | str | './tmp' | Directory for temporary files |

## SlurmRunner

The `SlurmRunner` executes jobs on a Slurm cluster.

```python
class SlurmRunner(BaseRunner):
    def __init__(self, 
                 partition: str,
                 time_limit: str = "01:00:00",
                 memory: str = "4G",
                 cpus_per_task: int = 1,
                 config: Dict[str, Any] = None):
        """
        Initialize a new SlurmRunner.
        
        Args:
            partition: Slurm partition to use
            time_limit: Time limit for jobs (format: HH:MM:SS)
            memory: Memory allocation for jobs
            cpus_per_task: Number of CPUs per task
            config: Additional configuration
        """
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `modules` | List[str] | [] | Modules to load in the Slurm job |
| `sbatch_options` | Dict[str, str] | {} | Additional options for sbatch |

## PanDARunner

The `PanDARunner` executes jobs on the PanDA distributed computing system.

```python
class PanDARunner(BaseRunner):
    def __init__(self, 
                 site: str,
                 queue: str,
                 config: Dict[str, Any] = None):
        """
        Initialize a new PanDARunner.
        
        Args:
            site: PanDA site to use
            queue: PanDA queue to use
            config: Additional configuration
        """
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `container_image` | str | None | Container image to use for jobs |
| `resource_type` | str | 'GRID' | PanDA resource type |

## Example Usage

### JobLibRunner

```python
from scheduler import JobLibRunner

# Create a runner for local parallel execution
runner = JobLibRunner(
    n_jobs=4,  # Use 4 cores
    backend='loky',  # Use the loky backend
    config={
        'tmp_dir': './job_tmp'  # Use a custom temp directory
    }
)
```

### SlurmRunner

```python
from scheduler import SlurmRunner

# Create a runner for Slurm execution
runner = SlurmRunner(
    partition="compute",
    time_limit="02:00:00",  # 2 hours
    memory="8G",
    cpus_per_task=4,
    config={
        'modules': ['python/3.9', 'singularity'],
        'sbatch_options': {
            'account': 'my-project',
            'mail-user': 'user@example.com',
            'mail-type': 'END,FAIL'
        }
    }
)
```

### PanDARunner

```python
from scheduler import PanDARunner

# Create a runner for PanDA execution
runner = PanDARunner(
    site="CERN-PROD",
    queue="ATLAS",
    config={
        'container_image': 'docker://atlas/athena:latest',
        'resource_type': 'GRID'
    }
)
```
