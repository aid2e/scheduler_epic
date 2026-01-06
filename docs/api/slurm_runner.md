# SlurmRunner

*Defined in [`scheduler.runners.slurm_runner`](https://github.com/aid2e/scheduler_epic/blob/main/scheduler/runners/slurm_runner.py)*

Strict Slurm Runner that only executes user-provided scripts
using a user-supplied SLURM template.

## Class Definition

```python
class SlurmRunner(self, slurm_template: <class 'str'>, init_env: Optional[list] = None, source_dir: Optional[str] = None):
    """
    Initialize a new SlurmRunner.
    **Args:**
    * **slurm_template**: Path to the SLURM template file to use for job submission.
    * **init_env**: Optional list of environment setup commands to run before job execution.
    * **source_dir**: Optional source directory to include in the job environment.
    
    **Raises:**
    * **FileNotFoundError**: If the SLURM template file does not exist.
    """
```

## Methods

| Method | Description |
|--------|-------------|
| [`cancel_job`](#cancel_job) | Cancel a job that has been submitted to Slurm. |
| [`check_job_status`](#check_job_status) | Check the current status of a submitted job. |
| [`run_job`](#run_job) | Submit a job to the Slurm cluster. |

## Method Details

### cancel_job

```python
def cancel_job(self, job: <class 'Job'>) -> Any
```

Cancel a job that has been submitted to Slurm.
Sends a signal to the Slurm scheduler to terminate the job and updates
the job state to CANCELLED.
**Args:**
* **job**: The Job object to cancel.

---

### check_job_status

```python
def check_job_status(self, job: <class 'Job'>) -> Any
```

Check the current status of a submitted job.
Queries the Slurm scheduler to determine if the job is pending, running,
or completed. Updates the job state and collects results if the job
has finished execution.
**Args:**
* **job**: The Job object whose status should be checked.

---

### run_job

```python
def run_job(self, job: <class 'Job'>) -> Any
```

Submit a job to the Slurm cluster.
Prepares the job environment, generates necessary scripts, and submits
the job to Slurm using sbatch. Updates job state and internal ID upon
successful submission.
**Args:**
* **job**: The Job object to submit. Must have job_type of FUNCTION or SCRIPT.

**Raises:**
* **NotImplementedError**: If job type is SCRIPT or CONTAINER (not supported).
* **ValueError**: If job type is unsupported.

