# SlurmRunner

*Defined in [`scheduler.runners.slurm_runner`](https://github.com/aid2e/scheduler_epic/blob/main/scheduler/runners/slurm_runner.py)*

A runner that submits jobs to a Slurm cluster.
This runner creates temporary job scripts and submits them to Slurm.
It can handle different job types:
- Function: Serializes and runs Python functions
- Script: Executes scripts directly
- Container: Runs containers using Singularity

**Inherits from:** [BaseRunner](baserunner.md)

## Class Definition

```python
class SlurmRunner(self, partition: <class 'str'> = batch, time_limit: <class 'str'> = 01:00:00, memory: <class 'str'> = 4G, cpus_per_task: <class 'int'> = 1, config: Dict[str, Any] = None):
    """
    Initialize a new SlurmRunner.
    **Args:**
    * **partition**: Slurm partition to submit jobs to
    * **time_limit**: Time limit for jobs (HH:MM:SS)
    * **memory**: Memory to allocate per job
    * **cpus_per_task**: Number of CPUs to allocate per job
    * **config**: Additional configuration options:
    * **modules**: List of modules to load (default: ['python'])
    * **singularity_path**: Path to singularity executable (default: 'singularity')
    * **job_dir**: Directory to store job files (default: ~/slurm_jobs)
    """
```

## Methods

| Method | Description |
|--------|-------------|
| [`cancel_job`](#cancel_job) | Cancel a job. |
| [`check_job_status`](#check_job_status) | Check the status of a job and update its state. |
| [`run_job`](#run_job) | Submit a job to Slurm. |

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

Submit a job to Slurm.
**Args:**
* **job**: The job to run

