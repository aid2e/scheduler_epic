# Trial

*Defined in [`scheduler.trial.trial`](https://github.com/aid2e/scheduler_epic/blob/main/scheduler/trial/trial.py)*

A trial class that extends Ax trial functionality.
A trial can contain multiple jobs and has a state that is tracked.

## Class Definition

```python
class Trial(self, trial_id: <class 'str'>, parameters: Dict[str, Any]):
    """
    Initialize a new trial.
    **Args:**
    * **trial_id**: Unique identifier for the trial
    * **parameters**: Dictionary of parameters for this trial
    """
```

## Methods

| Method | Description |
|--------|-------------|
| [`add_job`](#add_job) | Add a job to this trial. |
| [`check_status`](#check_status) | Check the status of all jobs and update the trial state. |
| [`get_results`](#get_results) | Gather results from all jobs. |
| [`run`](#run) | Run all jobs in this trial. |

## Method Details

### add_job

```python
def add_job(self, job: <class 'Job'>) -> None
```

Add a job to this trial.
**Args:**
* **job**: The job to add

---

### check_status

```python
def check_status(self) -> <enum 'TrialState'>
```

Check the status of all jobs and update the trial state.
**Returns:**
  The current state of the trial

---

### get_results

```python
def get_results(self) -> Dict[str, Any]
```

Gather results from all jobs.
**Returns:**
  Dictionary of results

---

### run

```python
def run(self) -> None
```

Run all jobs in this trial.

