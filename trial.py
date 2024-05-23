import joblib
import argparse
import os
import subprocess
import json
from ax.core import Experiment
from ax.service.scheduler import Scheduler, SchedulerOptions
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    """
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

def run_dd_web_display(script_path: str, output_file: str):
    command = f"dd_web_display -o {output_file} --export {script_path}"
    print("Running command:", command)
    subprocess.run(command, shell=True, check=True)

def run_script(script_path: str, output_file: str):
    run_dd_web_display(script_path, output_file)
    return output_file

class JoblibQueueClient:
    def __init__(self, n_jobs: int = 1):
        self.jobs = {}
        self.total_jobs = 0
        self.n_jobs = n_jobs

    def schedule_job_with_parameters(self, script_path: str, output_file: str):
        print(f"Scheduling job for script: {script_path}")
        job = joblib.delayed(run_script)(script_path, output_file)
        job_id = self.total_jobs
        self.jobs[job_id] = job
        print(f"Job {job_id} submitted to joblib.")
        self.total_jobs += 1
        return job_id

    def run_jobs(self):
        print("Running scheduled jobs...")
        joblib.Parallel(n_jobs=self.n_jobs)(job for job in self.jobs.values())
        print("All jobs completed.")

JOB_QUEUE_CLIENT = JoblibQueueClient(n_jobs=-1)

def main():
    parser = argparse.ArgumentParser(description="Run a specified XML script with joblib.")
    parser.add_argument('--config', type=str, help='Path to the configuration file.', default='config.json')
    args = parser.parse_args()

    config = load_config(args.config)
    script_path = config["scripts"]
    output_file = config["output_file"]

    JOB_QUEUE_CLIENT.schedule_job_with_parameters(script_path, output_file)
    JOB_QUEUE_CLIENT.run_jobs()

if __name__ == "__main__":
    main()
