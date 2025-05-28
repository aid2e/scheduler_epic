# AxScheduler

The `AxScheduler` class is the main entry point for using the Scheduler library. It integrates with Ax for optimization and manages the execution of trials.

## Class Definition

```python
class AxScheduler:
    def __init__(self, 
                 ax_client_or_experiment: Union[AxClient, Experiment], 
                 runner: BaseRunner, 
                 config: Dict[str, Any] = None):
        """
        Initialize a new AxScheduler.
        
        Args:
            ax_client_or_experiment: The Ax client or experiment to use for optimization
            runner: The runner to use for executing jobs
            config: Additional configuration options
        """
```

## Key Methods

### Setting Objective Functions

```python
def set_objective_function(self, function: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
    """
    Set the objective function to use for trials.
    
    Args:
        function: A function that takes a dict of parameters and returns a dict of metrics
    """
```

```python
def set_script_objective(self, script_path: str, script_options: Dict[str, Any] = None) -> None:
    """
    Set a script as the objective function.
    
    Args:
        script_path: Path to the script to run
        script_options: Additional options for script execution
    """
```

```python
def set_container_objective(self, container_image: str, container_command: str,
                         container_options: Dict[str, Any] = None) -> None:
    """
    Set a container as the objective function.
    
    Args:
        container_image: Container image to run
        container_command: Command to run in the container
        container_options: Additional options for container execution
    """
```

### Running Optimization

```python
def run_optimization(self, max_trials: int = 10, timeout: Optional[float] = None,
                  synchronous: Optional[bool] = None) -> Dict[str, Any]:
    """
    Run the optimization process.
    
    Args:
        max_trials: Maximum number of trials to run
        timeout: Maximum time to run the optimization (in seconds)
        synchronous: Whether to run trials synchronously

    Returns:
        The best parameters found
    """
```

### Batch Trial Submission

```python
@contextmanager
def batch_trial_context(self) -> "BatchTrialContext":
    """
    Context manager for batch trial submission.
    
    Usage:
        with scheduler.batch_trial_context() as batch:
            batch.add_trial({"x": 0.1, "y": 0.2})
            batch.add_trial({"x": 0.3, "y": 0.4})
    """
```

### Experiment Persistence

```python
def save_experiment(self, path: str) -> None:
    """
    Save the current experiment to a file.
    
    Args:
        path: Path to save the experiment to
    """
```

```python
def load_experiment(self, path: str) -> None:
    """
    Load an experiment from a file.
    
    Args:
        path: Path to load the experiment from
    """
```

## Configuration Options

The `AxScheduler` accepts a configuration dictionary with the following options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `monitoring_interval` | int | 10 | Seconds between status checks |
| `job_output_dir` | str | './outputs' | Directory for job outputs |
| `synchronous` | bool | True | Run trials synchronously |
| `cleanup_after_completion` | bool | True | Clean up files after completion |

## Example Usage

```python
# Create a scheduler with custom configuration
scheduler = AxScheduler(
    ax_client, 
    runner,
    config={
        'monitoring_interval': 5,  # Check status every 5 seconds
        'job_output_dir': './trial_outputs',  # Custom output directory
        'synchronous': False,  # Run trials asynchronously
    }
)

# Set the objective function
scheduler.set_objective_function(my_objective_function)

# Run the optimization
best_params = scheduler.run_optimization(max_trials=20)
```
