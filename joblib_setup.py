import joblib
from ax.core.base_trial import TrialStatus
import numpy as np
import os
import json
import subprocess
from typing import Any, Dict, NamedTuple, Union


# def load_config():
#     """
#     Load configuration from a JSON file located in the same directory as the script.
#     """
#     config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
#     with open(config_path, 'r') as config_file:
#         return json.load(config_file)
def load_config(config_path):
    """
    Load configuration from a JSON file.
    """
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

def run_dd_web_display(script_path, output_file):
    command = f"dd_web_display -o {output_file} --export {script_path} -k"
    print("running command: ", command)
    subprocess.run(command, shell=True, check=True)

def run_script(script_path, output_file):
    """
    Checks for the presence of an EPIC directory in the script's current directory.
    If not found, it sources a setup script from the same location, as specified in the config.json.
    """
    try:
        # Load configuration
        config = load_config()

        # Determine the directory where the current script is located
        current_dir = os.path.dirname(os.path.realpath(__file__))

        # Check if the EPIC directory exists in the current directory
        epic_directory = os.path.join(current_dir, "epic")
        if not os.path.exists(epic_directory):
            print("EPIC directory not found. Setting up the environment...")
            setup_script = os.path.join(current_dir, config['setup_script'])
            # Source the setup script to configure the environment
            subprocess.check_call(f"source {setup_script}", shell=True, executable='/bin/bash')

        # Execute the script using the same path as epic_executable
        output = subprocess.check_output([script_path], stderr=subprocess.STDOUT)
        print(f"Script {script_path} executed successfully, output at {output_file}")
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"An error occurred while executing the script: {e.output.decode('utf-8')}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


class JoblibJob(NamedTuple):
    id: int
    job: joblib.parallel.BatchedCalls

class JoblibQueueClient:
    def __init__(self, n_jobs: int = 1):
        self.jobs = {}
        self.total_jobs = 0
        self.n_jobs = n_jobs

    def schedule_job_with_parameters(self, script_path):
        print(f"Scheduling job for script: {script_path}")
        job = joblib.delayed(run_script)(script_path)
        job_id = self.total_jobs
        self.jobs[job_id] = JoblibJob(job_id, job)
        print(f"Job {job_id} submitted to joblib.")
        self.total_jobs += 1
        return job_id


    # def schedule_job_with_parameters(self, job_func, params):
    #     job = self.submit_joblib_job(job_func, params)
    #     self.total_jobs += 1
    #     return job.id


    def run_jobs(self):
        print("Running scheduled jobs...")
        results = joblib.Parallel(n_jobs=self.n_jobs)(job.job for job in self.jobs.values())
        for job_id, result in enumerate(results):
            print(f"Job {job_id} completed.")
            self.jobs[job_id].result = result

    def get_job_status(self, job_id):
        if job_id not in self.jobs:
            return TrialStatus.FAILED
        return TrialStatus.COMPLETED if hasattr(self.jobs[job_id], 'result') else TrialStatus.RUNNING

    def get_outcome_value_for_completed_job(self, job_id):
        if job_id not in self.jobs or not hasattr(self.jobs[job_id], 'result'):
            return {}
        # Process the result as needed
        return {'result': self.jobs[job_id].result}

JOB_QUEUE_CLIENT = JoblibQueueClient(n_jobs=-1)  # Set the number of parallel jobs

def get_joblib_queue_client():
    return JOB_QUEUE_CLIENT

# from joblib import Parallel, delayed
# from random import randint
# from time import time
# from typing import Any, Dict, NamedTuple, Union

# from ax.core.base_trial import TrialStatus
# from ax.utils.measurement.synthetic_functions import branin


# class Joblib(NamedTuple):
#     """class to represent a job scheduled on `MockJobQueue`."""
#     id: int
#     parameters: Dict[str, Union[str, float, int, bool]]


# class JoblibQueueClient:
#     """Dummy class to represent a job queue where the Ax `Scheduler` will
#     deploy trial evaluation runs during optimization.
#     """
#     jobs: Dict[int, Joblib] = {}

#     def schedule_job_with_parameters(
#         self, parameters: Dict[str, Union[str, float, int, bool]]
#     ) -> int:
#         """Schedules an evaluation job with given parameters and returns job ID."""
#         job_id = int(time() * 1e6)
#         self.jobs[job_id] = Joblib(job_id, parameters)
#         return job_id

#     def get_job_status(self, job_id: int) -> TrialStatus:
#         """Get status of the job by a given ID. For simplicity of the example,
#         return an Ax `TrialStatus`.
#         """
#         job = self.jobs[job_id]
#         # Check if job is running or completed (for simplicity, random status)
#         if randint(0, 3) > 0:
#             return TrialStatus.COMPLETED
#         return TrialStatus.RUNNING

#     def get_outcome_value_for_completed_job(self, job_id: int) -> Dict[str, float]:
#         """Get evaluation results for a given completed job."""
#         job = self.jobs[job_id]
#         # Simulated function call instead of actual container and script execution
#         return {"branin": branin(job.parameters.get("x1"), job.parameters.get("x2"))}

#     def run_joblib_execution(self, parameters: Dict[str, Union[str, float, int, bool]]) -> Dict[str, float]:
#         """Run the execution using joblib, simulating container loading and script execution."""
#         # Simulating container loading
#         print("Loading EPIC container...")

#         # Run scripts in parallel using joblib
#         results = Parallel(n_jobs=-1)(
#             delayed(self._run_script)(parameters, i) for i in range(5)
#         )

#         # Aggregate results (assuming the average here for simplicity)
#         return {"result": sum(results) / len(results)}

#     def _run_script(self, parameters: Dict[str, Union[str, float, int, bool]], script_id: int) -> float:
#         """Simulate running a script and return a result."""
#         print(f"Running script {script_id} with parameters {parameters}")
#         return branin(parameters.get("x1"), parameters.get("x2"))


# MOCK_JOB_QUEUE_CLIENT = JoblibQueueClient()


# def get_mock_job_queue_client() -> JoblibQueueClient:
#     """Obtain the singleton job queue instance."""
#     return MOCK_JOB_QUEUE_CLIENT


# # Example usage:
# if __name__ == "__main__":
#     client = get_mock_job_queue_client()
#     parameters = {"x1": 2.5, "x2": 7.5}
#     job_id = client.schedule_job_with_parameters(parameters)
    
#     # Simulate waiting for the job to complete
#     import time
#     while client.get_job_status(job_id) != TrialStatus.COMPLETED:
#         time.sleep(1)
    
#     # Get the job outcome
#     result = client.get_outcome_value_for_completed_job(job_id)
#     print(f"Job {job_id} result: {result}")
    
#     # Run joblib execution
#     joblib_result = client.run_joblib_execution(parameters)
#     print(f"Joblib execution result: {joblib_result}")
