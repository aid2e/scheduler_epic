# JobLibRunner

*Defined in [`scheduler.runners.joblib_runner`](https://github.com/aid2e/scheduler_epic/blob/main/scheduler/runners/joblib_runner.py)*

A runner that uses joblib for parallel execution.
This runner is suitable for local execution with multiple cores.
It can handle different job types:
- Function: Uses joblib to run Python functions
- Script: Executes scripts in separate processes
- Container: Runs containers using Docker or Singularity

**Inherits from:** [BaseRunner](base_runner.md)

## Class Definition

```python
class JobLibRunner(self, n_jobs: <class 'int'> = -1, backend: <class 'str'> = loky, config: Dict[str, Any] = None):
    """
    Initialize a new JobLibRunner.
    **Args:**
    * **n_jobs**: Number of jobs to run in parallel (-1 for all cores)
    * **backend**: Backend to use for joblib (loky, threading, multiprocessing)
    * **config**: Additional configuration options:
    * **container_engine**: 'docker' or 'singularity' (default: 'docker')
    * **tmp_dir**: Directory for temporary files (default: system temp dir)
    """
```

## Methods

| Method | Description |
|--------|-------------|
| [`cancel_job`](#cancel_job) | Cancel a job. |
| [`check_job_status`](#check_job_status) | Check the status of a job and update its state. |
| [`run_job`](#run_job) | Run a job using the appropriate execution method. |
| [`shutdown`](#shutdown) | Shutdown the executor. |

## Method Details

### cancel_job

```python
def cancel_job(self, job: Any) -> None
```

Cancel a job.
**Args:**
* **job**: The job to cancel

---

### check_job_status

```python
def check_job_status(self, job: Any) -> None
```

Check the status of a job and update its state.
**Args:**
* **job**: The job to check

---

### run_job

```python
def run_job(self, job: Any) -> None
```

Run a job using the appropriate execution method.
**Args:**
* **job**: The job to run

---

### shutdown

```python
def shutdown(self) -> Any
```

Shutdown the executor.

