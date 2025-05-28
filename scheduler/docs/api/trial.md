# Trial

The `Trial` class represents an optimization trial that contains one or more jobs. It extends the functionality of Ax trials with additional features for state tracking and job management.

## Class Definition

```python
class Trial:
    def __init__(self, trial_id: str, parameters: Dict[str, Any]):
        """
        Initialize a new trial.
        
        Args:
            trial_id: Unique identifier for the trial
            parameters: Dictionary of parameters for this trial
        """
```

## Trial States

The `TrialState` enum defines the possible states of a trial:

```python
class TrialState(Enum):
    """Possible states for a trial."""
    CREATED = "created"      # Trial has been created
    QUEUED = "queued"        # Trial is in the queue
    RUNNING = "running"      # Trial is currently running
    COMPLETED = "completed"  # Trial has completed successfully
    FAILED = "failed"        # Trial has failed
    CANCELLED = "cancelled"  # Trial was cancelled
```

## Key Methods

### Job Management

```python
def add_job(self, job: Job) -> None:
    """
    Add a job to this trial.
    
    Args:
        job: The job to add
    """
```

### Trial Execution

```python
def run(self) -> None:
    """
    Run all jobs in this trial.
    """
```

### Result Handling

```python
def set_results(self, results: Dict[str, Any]) -> None:
    """
    Set the results of this trial.
    
    Args:
        results: Dictionary of metric results
    """
```

```python
def get_results(self) -> Dict[str, Any]:
    """
    Get the results of this trial.
    
    Returns:
        Dictionary of metric results
    """
```

### State Management

```python
def update_state(self, state: TrialState) -> None:
    """
    Update the state of this trial.
    
    Args:
        state: The new state
    """
```

```python
def check_status(self) -> TrialState:
    """
    Check the status of this trial by checking all jobs.
    
    Returns:
        The current state of the trial
    """
```

## Trial Timing

Trials track timing information:

- `creation_time`: When the trial was created
- `start_time`: When the trial started running
- `end_time`: When the trial completed (successfully or not)

```python
def get_duration(self) -> Optional[float]:
    """
    Get the duration of this trial in seconds.
    
    Returns:
        Duration in seconds, or None if the trial hasn't completed
    """
```

## Example Usage

```python
from scheduler import Trial, Job, JobType, TrialState

# Create a trial
trial = Trial(trial_id="trial1", parameters={"x": 0.5, "y": 0.7})

# Add a job to the trial
job = Job(
    job_id="job1",
    job_type=JobType.FUNCTION,
    function=my_objective_function,
    params=trial.parameters
)
trial.add_job(job)

# Run the trial
trial.run()

# Check if the trial is completed
if trial.state == TrialState.COMPLETED:
    results = trial.get_results()
    print(f"Trial completed with results: {results}")
```
