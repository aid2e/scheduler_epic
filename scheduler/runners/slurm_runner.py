# Copyright (C) 2024 AI&D 
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
import os
import stat
import subprocess
from typing import Dict, List, Optional, Tuple

from ..job import Job, JobStatus, JobStatusMap, JobStatusTerminal
from .base_runner import BaseRunner

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


class SlurmJob:
    """
    A class to represent a Slurm job.
    """

    def __init__(self, job_id: int, job_dir: str):
        self.job_id = job_id
        self.job_dir = job_dir
        self.status = JobStatus.submitted


class SlurmRunner(BaseRunner):
    """
    A runner to execute jobs on a Slurm cluster.
    This runner submits jobs using `sbatch` and monitors them with `squeue`.
    """

    def __init__(self, work_dir: str, **kwargs):
        """
        Initialize the Slurm runner.
        :param work_dir: The working directory for the jobs.
        :param kwargs: Additional arguments for the runner.
        """
        super().__init__(work_dir, **kwargs)
        self.jobs: Dict[str, SlurmJob] = {}
        _logger.info(f"SlurmRunner initialized with work_dir: {self.work_dir}")
        # Add any other Slurm-specific initializations here
        # For example, partition, account, etc.
        self.slurm_partition = kwargs.get("slurm_partition", "shared")
        self.slurm_account = kwargs.get("slurm_account", None)

    def _generate_sbatch_script(self, job: Job) -> str:
        """
        Generate the sbatch script for a given job.
        """
        job_dir = os.path.join(self.work_dir, str(job.trial.id))
        os.makedirs(job_dir, exist_ok=True)

        # This will be the script that `sbatch` executes.
        # It needs to execute the user's command.
        run_script_path = os.path.join(job_dir, "run_script.sh")
        with open(run_script_path, "w") as f:
            f.write("#!/bin/bash\n")
            # You can add environment setup here if needed
            # e.g., source /path/to/your/env/bin/activate
            f.write(f"cd {job_dir}\n")
            f.write(f"{job.trial.command}\n")
        
        # Make the script executable
        st = os.stat(run_script_path)
        os.chmod(run_script_path, st.st_mode | stat.S_IEXEC)

        # This is the sbatch script that will be submitted.
        sbatch_script_path = os.path.join(job_dir, "sbatch_script.sh")
        output_log = os.path.join(job_dir, "slurm.out")
        error_log = os.path.join(job_dir, "slurm.err")
        
        with open(sbatch_script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --job-name={job.trial.id}\n")
            f.write(f"#SBATCH --output={output_log}\n")
            f.write(f"#SBATCH --error={error_log}\n")
            f.write(f"#SBATCH --partition={self.slurm_partition}\n")
            if self.slurm_account:
                f.write(f"#SBATCH --account={self.slurm_account}\n")
            # Add other sbatch options as needed (e.g., nodes, ntasks, gpus)
            # f.write("#SBATCH --nodes=1\n")
            # f.write("#SBATCH --ntasks-per-node=1\n")
            
            f.write(f"srun {run_script_path}\n")

        return sbatch_script_path

    def schedule(self, jobs: List[Job]) -> None:
        """
        Schedule a list of jobs on the Slurm cluster.
        """
        for job in jobs:
            if job.trial.id in self.jobs:
                _logger.warning(f"Job {job.trial.id} already scheduled. Skipping.")
                continue

            sbatch_script = self._generate_sbatch_script(job)
            job_dir = os.path.dirname(sbatch_script)

            try:
                # Submit the job to Slurm
                cmd = ["sbatch", sbatch_script]
                _logger.info(f"Submitting job {job.trial.id} with command: {' '.join(cmd)}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=job_dir,
                )
                # Example output: "Submitted batch job 12345"
                slurm_job_id = int(result.stdout.strip().split()[-1])
                _logger.info(f"Job {job.trial.id} submitted to Slurm with ID: {slurm_job_id}")
                self.jobs[job.trial.id] = SlurmJob(job_id=slurm_job_id, job_dir=job_dir)
                job.status = JobStatus.submitted
            except (subprocess.CalledProcessError, IndexError, ValueError) as e:
                _logger.error(f"Failed to submit job {job.trial.id}: {e}")
                job.status = JobStatus.failed
                if isinstance(e, subprocess.CalledProcessError):
                    _logger.error(f"sbatch stderr: {e.stderr}")

    def get_status(self, jobs: List[Job]) -> None:
        """
        Get the status of a list of jobs from the Slurm queue.
        """
        job_ids_to_check = [
            str(self.jobs[j.trial.id].job_id)
            for j in jobs
            if j.trial.id in self.jobs and j.status not in JobStatusTerminal
        ]

        if not job_ids_to_check:
            return

        try:
            # Check job statuses with squeue
            cmd = ["squeue", "-h", "-j", ",".join(job_ids_to_check), "-o", "%i %t"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Create a map of Slurm job ID to status
            slurm_status_map = {}
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split()
                slurm_job_id, slurm_state = parts[0], parts[1]
                slurm_status_map[slurm_job_id] = slurm_state

        except subprocess.CalledProcessError as e:
            _logger.error(f"Failed to get job statuses from squeue: {e.stderr}")
            # If squeue fails, we can't update status, so we return.
            return

        for job in jobs:
            if job.trial.id not in self.jobs or job.status in JobStatusTerminal:
                continue

            slurm_job = self.jobs[job.trial.id]
            slurm_id_str = str(slurm_job.job_id)
            
            if slurm_id_str in slurm_status_map:
                # Job is still in queue or running
                slurm_state = slurm_status_map[slurm_id_str]
                # Map Slurm state to our JobStatus
                # Example mapping: PD -> pending, R -> running, CG -> running
                if slurm_state in ("PD",):
                    job.status = JobStatus.pending
                elif slurm_state in ("R", "CG"):
                    job.status = JobStatus.running
                else:
                    # Other states like F, CA, TO, etc., are considered finished/failed
                    # We will rely on checking the exit code for the final status
                    pass 
            else:
                # Job is no longer in squeue, so it's finished, failed, or cancelled.
                # We check the output/error logs or use `sacct` to be sure.
                # For simplicity, we'll check for an exit code file.
                exit_code_path = os.path.join(slurm_job.job_dir, "run_script.sh.exit_code") # This needs to be created by the run script
                if os.path.exists(exit_code_path):
                     with open(exit_code_path, "r") as f:
                        exit_code = int(f.read().strip())
                        job.status = JobStatus.finished if exit_code == 0 else JobStatus.failed
                else:
                    # If the exit code file doesn't exist, something might be wrong.
                    # Or the job was cancelled. We can assume failed for now.
                    job.status = JobStatus.failed

    def get_output(self, job: Job, task: str = "stdout", tail: Optional[int] = None) -> Optional[str]:
        """
        Get the output of a job.
        """
        if job.trial.id not in self.jobs:
            return None

        slurm_job = self.jobs[job.trial.id]
        log_file = "slurm.out" if task == "stdout" else "slurm.err"
        log_path = os.path.join(slurm_job.job_dir, log_file)

        if not os.path.exists(log_path):
            return None

        with open(log_path, "r") as f:
            if tail:
                lines = f.readlines()
                return "".join(lines[-tail:])
            else:
                return f.read()

    def cancel(self, jobs: List[Job]) -> None:
        """
        Cancel a list of jobs.
        """
        job_ids_to_cancel = [
            str(self.jobs[j.trial.id].job_id)
            for j in jobs
            if j.trial.id in self.jobs and j.status not in JobStatusTerminal
        ]

        if not job_ids_to_cancel:
            return

        try:
            cmd = ["scancel"] + job_ids_to_cancel
            subprocess.run(cmd, check=True)
            _logger.info(f"Cancelled jobs: {job_ids_to_cancel}")
            for job in jobs:
                if str(self.jobs[job.trial.id].job_id) in job_ids_to_cancel:
                    job.status = JobStatus.cancelled
        except subprocess.CalledProcessError as e:
            _logger.error(f"Failed to cancel jobs: {e}")
