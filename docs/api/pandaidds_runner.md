# PanDAiDDSRunner

*Defined in [`scheduler.runners.pandaidds_runner`](https://github.com/aid2e/scheduler_epic/blob/main/scheduler/runners/pandaidds_runner.py)*

A runner that submits jobs to the PanDA system.
This runner requires the PanDA client to be installed.

**Inherits from:** [BaseRunner](base_runner.md)

## Class Definition

```python
class PanDAiDDSRunner(self, name: <class 'str'> = None, cloud: <class 'str'> = US, queue: <class 'str'> = BNL_PanDA_1, vo: <class 'str'> = wlcg, init_env: <class 'str'> = None, source_dir: <class 'str'> = None, source_dir_parent_level: <class 'int'> = 1, exclude_source_files: <class 'list'> = [], max_walltime: <class 'int'> = 36000, core_count: <class 'int'> = 1, total_memory: <class 'int'> = 4000, enable_separate_log: <class 'bool'> = True, global_parameters: <class 'dict'> = {}, job_dir: <class 'str'> = None, funcs: <class 'dict'> = {}, deps: <class 'dict'> = {}, config: Dict[str, Any] = None):
    """
    Initialize a new PanDAiDDSRunner.
    **Args:**
    * **site**: Site to submit jobs to
    * **cloud**: Cloud to submit jobs to
    * **queue**: Queue to submit jobs to
    * **vo**: Virtual organization
    * **config**: Additional configuration options
    """
```

## Methods

| Method | Description |
|--------|-------------|
| [`cancel_job`](#cancel_job) | Cancel a job. |
| [`check_job_status`](#check_job_status) | Check the status of a job and update its state. |
| [`check_single_job_status`](#check_single_job_status) | Check the status of a single job and update its state. |
| [`run_job`](#run_job) | Run a job using the appropriate execution method. |
| [`submit_job`](#submit_job) |  |
| [`submit_workflow`](#submit_workflow) |  |

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

### check_single_job_status

```python
def check_single_job_status(self, job: Any) -> None
```

Check the status of a single job and update its state.
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

### submit_job

```python
def submit_job(self, job: Any) -> None
```

*No documentation available.*

---

### submit_workflow

```python
def submit_workflow(self, job: Any) -> <class 'object'>
```

*No documentation available.*

