# Job

The `Job` class represents a unit of work that can be executed by a runner. Jobs can be Python functions, scripts, or containers.

## Class Definition

```python
class Job:
    def __init__(self, 
                 job_id: str, 
                 job_type: JobType = JobType.FUNCTION,
                 function: Optional[Callable] = None, 
                 script_path: Optional[str] = None,
                 container_image: Optional[str] = None,
                 container_command: Optional[str] = None,
                 params: Dict[str, Any] = None,
                 env_vars: Dict[str, str] = None,
                 working_dir: Optional[str] = None,
                 output_files: Optional[List[str]] = None):
        """
        Initialize a new job.
        
        Args:
            job_id: Unique identifier for the job
            job_type: Type of job (FUNCTION, SCRIPT, or CONTAINER)
            function: The function to run for this job (if job_type is FUNCTION)
            script_path: Path to the script to run (if job_type is SCRIPT)
            container_image: Container image to run (if job_type is CONTAINER)
            container_command: Command to run in the container (if job_type is CONTAINER)
            params: Parameters to pass to the function or script
            env_vars: Environment variables to set for the job
            working_dir: Working directory for the job
            output_files: List of output files to capture
        """
```

## Job Types

The `JobType` enum defines the supported job types:

```python
class JobType(Enum):
    """Type of job to run."""
    FUNCTION = "function"  # Python function
    SCRIPT = "script"      # Shell script or Python script
    CONTAINER = "container"  # Docker/Singularity container
```

## Job States

The `JobState` enum defines the possible states of a job:

```python
class JobState(Enum):
    """Possible states for a job."""
    CREATED = "created"    # Job has been created
    QUEUED = "queued"      # Job is in the queue
    RUNNING = "running"    # Job is currently running
    COMPLETED = "completed"  # Job has completed successfully
    FAILED = "failed"      # Job has failed
    CANCELLED = "cancelled"  # Job was cancelled
```

## Key Methods

### Job Execution

```python
def run(self, runner: "BaseRunner") -> None:
    """
    Run this job using the provided runner.
    
    Args:
        runner: The runner to use for execution
    """
```

### Result Handling

```python
def set_result(self, result: Any) -> None:
    """
    Set the result of this job.
    
    Args:
        result: The result of the job
    """
```

```python
def get_result(self) -> Any:
    """
    Get the result of this job.
    
    Returns:
        The result of the job
    """
```

### State Management

```python
def update_state(self, state: JobState) -> None:
    """
    Update the state of this job.
    
    Args:
        state: The new state
    """
```

## Example Usage

### Function Job

```python
from scheduler import Job, JobType

# Create a function job
def my_function(x, y):
    return x + y

job = Job(
    job_id="job1",
    job_type=JobType.FUNCTION,
    function=my_function,
    params={"x": 1, "y": 2}
)
```

### Script Job

```python
# Create a script job
job = Job(
    job_id="job2",
    job_type=JobType.SCRIPT,
    script_path="./my_script.py",
    params={"input_file": "data.csv", "output_file": "results.csv"},
    env_vars={"DEBUG": "1"}
)
```

### Container Job

```python
# Create a container job
job = Job(
    job_id="job3",
    job_type=JobType.CONTAINER,
    container_image="python:3.9",
    container_command="python /app/script.py",
    params={"threshold": 0.5},
    working_dir="/app",
    output_files=["results.json"]
)
```
