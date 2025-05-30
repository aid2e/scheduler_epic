# AxScheduler

*Defined in [`scheduler.ax_scheduler`](https://github.com/aid2e/scheduler_epic/blob/main/scheduler/ax_scheduler.py)*

A scheduler that integrates with Ax for optimization.
This scheduler allows running Ax trials using different runners.

## Class Definition

```python
class AxScheduler(self, ax_client_or_experiment: Union[ax.service.ax_client.AxClient, ax.core.experiment.Experiment], runner: <class 'BaseRunner'>, config: Dict[str, Any] = None):
    """
    Initialize a new AxScheduler.
    **Args:**
    * **ax_client_or_experiment**: The Ax client or experiment to use for optimization
    * **runner**: The runner to use for executing jobs
    * **config**: Additional configuration options:
    * **monitoring_interval**: Seconds between monitoring checks (default: 10)
    * **max_trial_monitoring_time**: Maximum time to monitor a trial in seconds (default: 86400 = 24 hours)
    * **job_output_dir**: Directory to store job outputs (default: ~/ax_scheduler_output)
    * **cleanup_after_completion**: Whether to clean up job files after completion (default: False)
    * **synchronous**: Whether to run trials synchronously (default: False)
    """
```

## Methods

| Method | Description |
|--------|-------------|
| [`batch_trial_context`](#batch_trial_context) | Context manager for creating and running a batch of trials. |
| [`complete_trial`](#complete_trial) | Mark a trial as completed in Ax. |
| [`get_next_trial`](#get_next_trial) | Generate a new trial using Ax and return its index. |
| [`load_experiment`](#load_experiment) | Load an experiment from a file. |
| [`monitor_trials`](#monitor_trials) | Monitor all running trials. |
| [`run_optimization`](#run_optimization) | Run the optimization process. |
| [`run_trial`](#run_trial) | Run a specific trial. |
| [`save_experiment`](#save_experiment) | Save the experiment to a file. |
| [`set_container_objective`](#set_container_objective) | Set a container to use as the objective function. |
| [`set_objective_function`](#set_objective_function) | Set the objective function to optimize. |
| [`set_script_objective`](#set_script_objective) | Set a script to use as the objective function. |

## Method Details

### batch_trial_context

```python
def batch_trial_context(self) -> Any
```

Context manager for creating and running a batch of trials.
This is useful for running multiple trials in parallel.
Example:
    ```python
    with scheduler.batch_trial_context() as batch:
        for i in range(5):
            params = {'x': i * 0.1, 'y': i * 0.2}
            batch.add_trial(params)
        batch.run()
    ```

---

### complete_trial

```python
def complete_trial(self, trial_index: <class 'int'>, raw_data: Optional[Dict[str, Any]] = None) -> None
```

Mark a trial as completed in Ax.
**Args:**
* **trial_index**: The index of the trial to complete
* **raw_data**: Raw data to attach to the trial

---

### get_next_trial

```python
def get_next_trial(self) -> Optional[int]
```

Generate a new trial using Ax and return its index.
**Returns:**
  The index of the new trial, or None if no more trials can be generated

---

### load_experiment

```python
def load_experiment(self, path: <class 'str'>) -> None
```

Load an experiment from a file.
**Args:**
* **path**: Path to load the experiment from

---

### monitor_trials

```python
def monitor_trials(self) -> None
```

Monitor all running trials.

---

### run_optimization

```python
def run_optimization(self, max_trials: <class 'int'> = 10) -> Dict[str, Any]
```

Run the optimization process.
**Args:**
* **max_trials**: Maximum number of trials to run

**Returns:**
  The best parameters found

---

### run_trial

```python
def run_trial(self, trial_index: <class 'int'>) -> <class 'Trial'>
```

Run a specific trial.
**Args:**
* **trial_index**: The index of the trial to run

**Returns:**
  The Trial object

---

### save_experiment

```python
def save_experiment(self, path: <class 'str'>) -> None
```

Save the experiment to a file.
**Args:**
* **path**: Path to save the experiment to

---

### set_container_objective

```python
def set_container_objective(self, container_image: <class 'str'>, container_command: Optional[str] = None) -> Any
```

Set a container to use as the objective function.
**Args:**
* **container_image**: Container image to run for each trial
* **container_command**: Command to run in the container (optional)

---

### set_objective_function

```python
def set_objective_function(self, objective_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Any
```

Set the objective function to optimize.
**Args:**
* **objective_fn**: The objective function to optimize

---

### set_script_objective

```python
def set_script_objective(self, script_path: <class 'str'>) -> Any
```

Set a script to use as the objective function.
**Args:**
* **script_path**: Path to the script to run for each trial

