# Job

*Defined in [`scheduler.job.job`](https://github.com/aid2e/scheduler_epic/blob/main/scheduler/job/job.py)*

A job that can be run by a runner.
Each job has a state that is tracked. Jobs can be one of several types:
- Function: A Python function to run
- Script: A shell or Python script to execute
- Container: A container to run

## Class Definition

```python
class Job(self, job_id: <class 'str'>, job_type: <enum 'JobType'> = JobType.FUNCTION, function: Optional[Callable] = None, script_path: Optional[str] = None, container_image: Optional[str] = None, container_command: Optional[str] = None, params: Dict[str, Any] = None, env_vars: Dict[str, str] = None, working_dir: Optional[str] = None, output_files: Optional[List[str]] = None):
    """
    Initialize a new job.
    **Args:**
    * **job_id**: Unique identifier for the job
    * **job_type**: Type of job (FUNCTION, SCRIPT, or CONTAINER)
    * **function**: The function to run for this job (if job_type is FUNCTION)
    * **script_path**: Path to the script to run (if job_type is SCRIPT)
    * **container_image**: Container image to run (if job_type is CONTAINER)
    * **container_command**: Command to run in the container (if job_type is CONTAINER)
    * **params**: Parameters to pass to the function or script
    * **env_vars**: Environment variables to set for the job
    * **working_dir**: Working directory for the job
    * **output_files**: List of output files to collect after job completion
    """
```

## Methods

| Method | Description |
|--------|-------------|
| [`complete`](#complete) | Mark the job as completed and store its results. |
| [`fail`](#fail) | Mark the job as failed and store the error. |
| [`get_results`](#get_results) | Get the results of this job. |
| [`has_failed`](#has_failed) | Check if the job has failed. |
| [`is_completed`](#is_completed) | Check if the job is completed. |
| [`is_running`](#is_running) | Check if the job is running. |
| [`run`](#run) | Run this job using its assigned runner. |
| [`set_runner`](#set_runner) | Set the runner for this job. |

## Method Details

### complete

```python
def complete(self, results: Dict[str, Any]) -> None
```

Mark the job as completed and store its results.
**Args:**
* **results**: The results of the job

---

### fail

```python
def fail(self, error: Optional[str] = None) -> None
```

Mark the job as failed and store the error.
**Args:**
* **error**: The error that caused the job to fail

---

### get_results

```python
def get_results(self) -> Dict[str, Any]
```

Get the results of this job.
**Returns:**
  Dictionary of results

---

### has_failed

```python
def has_failed(self) -> <class 'bool'>
```

Check if the job has failed.
**Returns:**
  True if the job has failed, False otherwise

---

### is_completed

```python
def is_completed(self) -> <class 'bool'>
```

Check if the job is completed.
**Returns:**
  True if the job is completed, False otherwise

---

### is_running

```python
def is_running(self) -> <class 'bool'>
```

Check if the job is running.
**Returns:**
  True if the job is running, False otherwise

---

### run

```python
def run(self) -> None
```

Run this job using its assigned runner.
**Raises:**
* **ValueError**: If no runner has been assigned

---

### set_runner

```python
def set_runner(self, runner: Any) -> None
```

Set the runner for this job.
**Args:**
* **runner**: The runner to use for this job

