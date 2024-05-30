import os
import subprocess
import json
import joblib
from joblib import Parallel, delayed
from typing import NamedTuple
import sys


def load_config(config_path):
    """
    Load configuration from a JSON file.
    """
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

def setup_environment():
    """
    Setup the environment if the EPIC directory is not found.
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    epic_directory = os.path.join(current_dir, "epic")

    if not os.path.exists(epic_directory):
        print("EPIC directory not found. Setting up the environment...")
        config_path = os.path.join(current_dir, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            setup_script = os.path.join(current_dir, config['setup_script'])
        else:
            setup_script = os.path.join(current_dir, 'default_setup.sh')
        
        print(f"Sourcing setup script: {setup_script}")
        subprocess.run(f"bash -c 'source {setup_script}'", shell=True, executable='/bin/bash')
        print("Environment setup completed.")

def run_user_script(script_path):
    """
    Run the user-provided script.
    """
    # command = "singularity run " + os.getenv("SINGULARITY_PATH", "/sciclone/home/hnayak/scheduler/local/lib/jug_xl-nightly.sif ") + "bash " + script_path
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
    config = load_config(config_path)
    path_to_sif = config["path_to_sif_image"]

    # Determine the appropriate interpreter based on the script extension
    if script_path.endswith('.sh'):
        interpreter = 'bash'
    else:
        raise ValueError(f"Unsupported script type: {script_path}")

    command = f"singularity run {os.getenv('SINGULARITY_PATH', path_to_sif)} {interpreter} {script_path}"
    subprocess.call(command.split())
    # command = "singularity run " + os.getenv("SINGULARITY_PATH", path_to_sif) + "bash " + script_path
    # subprocess.call(command.split(" "))


# Joblib components

class JoblibJob(NamedTuple):
    id: int
    job: joblib.parallel.BatchedCalls

class JoblibQueueClient:
    def __init__(self, n_jobs: int = 1):
        self.jobs = None
        self.total_jobs = 0
        self.n_jobs = n_jobs

    def schedule_job_with_parameters(self):
        #print(f"Scheduling job for script: {user_script}")
        #job = joblib.delayed(run_user_script)(user_script)
        self.jobs = Parallel(n_jobs=self.n_jobs, return_as = "generator")
        job_id = self.total_jobs
        #self.jobs[job_id] = JoblibJob(job_id, job)
        print(f"Job {job_id} submitted to joblib.")
        self.total_jobs += 1
        return job_id

    def run_jobs(self, user_script):
        print("Running scheduled jobs...")
        results = self.jobs(delayed(run_user_script)(user_script) for user_script in range(self.n_jobs))
        for job_id, result in enumerate(results):
            print(f"Job {job_id} completed.")
            self.jobs[job_id] = result

    def get_job_status(self, job_id):
        if job_id not in self.jobs:
            return "FAILED"
        return "COMPLETED" if hasattr(self.jobs[job_id], 'result') else "RUNNING"

    def get_outcome_value_for_completed_job(self, job_id):
        if job_id not in self.jobs or not hasattr(self.jobs[job_id], 'result'):
            return {}
        return {'result': self.jobs[job_id]}

JOB_QUEUE_CLIENT = JoblibQueueClient(n_jobs=4)  # Set the number of parallel jobs

def get_joblib_queue_client():
    return JOB_QUEUE_CLIENT

# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 load_container.py <user_script.py>")
        sys.exit(1)

    setup_environment()
    user_script_path = sys.argv[1]
    #run_eic_shell(user_script_path)
   
    job_id = JOB_QUEUE_CLIENT.schedule_job_with_parameters(user_script_path)
    job_id = 0
    JOB_QUEUE_CLIENT.run_jobs()
    print(f"Job {job_id} status: {JOB_QUEUE_CLIENT.get_job_status(job_id)}")
    print(f"Job {job_id} result: {JOB_QUEUE_CLIENT.get_outcome_value_for_completed_job(job_id)}")

