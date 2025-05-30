# BaseRunner

*Defined in [`scheduler.runners.base_runner`](https://github.com/aid2e/scheduler_epic/blob/main/scheduler/runners/base_runner.py)*

Abstract base class for job runners.
Runners are responsible for executing jobs on different
systems (local, Slurm, PanDA, etc.).

**Inherits from:** ABC

## Class Definition

```python
class BaseRunner(self, config: Dict[str, Any] = None):
    """
    Initialize a new runner.
    **Args:**
    * **config**: Configuration for the runner
    """
```

## Methods

| Method | Description |
|--------|-------------|
| [`cancel_job`](#cancel_job) | Cancel a job. |
| [`check_job_status`](#check_job_status) | Check the status of a job and update its state. |
| [`run_job`](#run_job) | Run a job. |

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

Run a job.
**Args:**
* **job**: The job to run

