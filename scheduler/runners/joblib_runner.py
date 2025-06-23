"""
JobLibRunner - Runner that uses joblib for parallel execution.
"""

import logging
import os
import joblib
import subprocess
import tempfile
import json
import shutil
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from ..job.job import JobType
from ..job.job_state import JobState
from .base_runner import BaseRunner


class JobLibRunner(BaseRunner):
    """
    A runner that uses joblib for parallel execution.

    This runner is suitable for local execution with multiple cores.
    It can handle different job types:
    - Function: Uses joblib to run Python functions
    - Script: Executes scripts in separate processes
    - Container: Runs containers using Docker or Singularity
    """

    def __init__(self, n_jobs: int = -1, backend: str = "loky", config: Dict[str, Any] = None):
        """
        Initialize a new JobLibRunner.

        Args:
            n_jobs: Number of jobs to run in parallel (-1 for all cores)
            backend: Backend to use for joblib (loky, threading, multiprocessing)
            config: Additional configuration options:
                container_engine: 'docker' or 'singularity' (default: 'docker')
                tmp_dir: Directory for temporary files (default: system temp dir)
        """
        super().__init__(config or {})
        self.n_jobs = n_jobs
        self.backend = backend
        self.running_jobs = {}  # job_id -> future
        self.executor = ThreadPoolExecutor(max_workers=os.cpu_count())

        # Container configuration
        self.container_engine = self.config.get("container_engine", "docker")
        self.tmp_dir = self.config.get("tmp_dir", tempfile.gettempdir())

        # Ensure temp directory exists
        os.makedirs(self.tmp_dir, exist_ok=True)

        self.logger = logging.getLogger("JoblibRunner")

    def _execute_function(self, job):
        """
        Execute a job's function with its parameters and update its state.

        Args:
            job: The job to execute

        Returns:
            The results of the function
        """
        try:
            # Set environment variables
            original_env = os.environ.copy()
            os.environ.update(job.env_vars)

            # Set working directory if specified
            original_dir = os.getcwd()
            if job.working_dir and os.path.isdir(job.working_dir):
                os.chdir(job.working_dir)

            try:
                # Wrap the function call with joblib.Parallel for potential speedup
                # if the function itself is parallelizable
                # parallel = joblib.Parallel(n_jobs=self.n_jobs, backend=self.backend)
                # results = parallel(joblib.delayed(job.function)(**job.params))
                results = joblib.Parallel(n_jobs=self.n_jobs, backend=self.backend)([joblib.delayed(job.function)(**job.params)])
                # Process results and mark job as completed
                if len(results) == 1:
                    # result_dict = {"result": results[0]}
                    result_dict = results[0]
                else:
                    # result_dict = {"results": results}
                    result_dict = results

                # Collect any output files if specified
                self._collect_output_files(job, result_dict)

                # job.complete(result_dict)     # should be done in check_job_status
                return result_dict
            finally:
                # Restore environment and directory
                os.environ.clear()
                os.environ.update(original_env)
                os.chdir(original_dir)

        except Exception as e:
            self.logger.error(f"Caught exception during execution job {job.job_id} function: {e}")
            # job.fail(str(e))
            return {"error": str(e)}

    def _execute_script(self, job):
        """
        Execute a script job.

        Args:
            job: The job to execute

        Returns:
            The results of the script
        """
        try:
            # Create a temporary directory for job execution
            job_dir = os.path.join(self.tmp_dir, f"job_{job.job_id}")
            os.makedirs(job_dir, exist_ok=True)

            # Create a file with the parameters
            params_file = os.path.join(job_dir, "params.json")
            with open(params_file, "w") as f:
                json.dump(job.params, f)

            # Build environment variables
            env = os.environ.copy()
            env.update(job.env_vars)
            env["JOB_PARAMS_FILE"] = params_file

            # Determine working directory
            working_dir = job.working_dir if job.working_dir else job_dir

            # Execute the script
            command = ["bash", job.script_path] if job.script_path.endswith(".sh") else ["python", job.script_path]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=working_dir,
                text=True,
            )

            stdout, stderr = process.communicate()

            # Check if the script was successful
            if process.returncode == 0:
                # Try to load results from a result file
                result_file = os.path.join(job_dir, "result.json")
                if os.path.exists(result_file):
                    with open(result_file, "r") as f:
                        result_dict = json.load(f)
                else:
                    # Use stdout as result
                    result_dict = {"stdout": stdout}

                # Collect any output files if specified
                self._collect_output_files(job, result_dict)

                # job.complete(result_dict)
                return result_dict
            else:
                error_msg = f"Script failed with exit code {process.returncode}. Error: {stderr}"
                # job.fail(error_msg)
                return {"error": error_msg}

        except Exception as e:
            # job.fail(str(e))
            return {"error": str(e)}
        finally:
            # Clean up temporary directory
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir)

    def _execute_container(self, job):
        """
        Execute a container job.

        Args:
            job: The job to execute

        Returns:
            The results of the container execution
        """
        try:
            # Create a temporary directory for job execution
            job_dir = os.path.join(self.tmp_dir, f"job_{job.job_id}")
            os.makedirs(job_dir, exist_ok=True)

            # Create a file with the parameters
            params_file = os.path.join(job_dir, "params.json")
            with open(params_file, "w") as f:
                json.dump(job.params, f)

            # Build the container command
            if self.container_engine == "docker":
                # Docker command
                cmd = ["docker", "run", "--rm"]

                # Add environment variables
                for key, value in job.env_vars.items():
                    cmd.extend(["-e", f"{key}={value}"])

                # Add volume mounts
                cmd.extend(["-v", f"{job_dir}:/job"])
                if job.working_dir:
                    cmd.extend(["-v", f"{job.working_dir}:/workdir"])
                    cmd.extend(["-w", "/workdir"])
                else:
                    cmd.extend(["-w", "/job"])

                # Add image and command
                cmd.append(job.container_image)

                if job.container_command:
                    cmd.extend(job.container_command.split())

            elif self.container_engine == "singularity":
                # Singularity command
                cmd = ["singularity", "run"]

                # Add environment variables
                for key, value in job.env_vars.items():
                    cmd.extend(["--env", f"{key}={value}"])

                # Add bind mounts
                cmd.extend(["--bind", f"{job_dir}:/job"])
                if job.working_dir:
                    cmd.extend(["--bind", f"{job.working_dir}:/workdir"])
                    cmd.extend(["--pwd", "/workdir"])
                else:
                    cmd.extend(["--pwd", "/job"])

                # Add image
                cmd.append(job.container_image)

                # Add command
                if job.container_command:
                    cmd.extend(["--app", job.container_command])
            else:
                raise ValueError(f"Unsupported container engine: {self.container_engine}")

            # Execute the container
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            stdout, stderr = process.communicate()

            # Check if the container execution was successful
            if process.returncode == 0:
                # Try to load results from a result file
                result_file = os.path.join(job_dir, "result.json")
                if os.path.exists(result_file):
                    with open(result_file, "r") as f:
                        result_dict = json.load(f)
                else:
                    # Use stdout as result
                    result_dict = {"stdout": stdout}

                # Collect any output files if specified
                self._collect_output_files(job, result_dict)

                # job.complete(result_dict)
                return result_dict
            else:
                error_msg = f"Container execution failed with exit code {process.returncode}. Error: {stderr}"
                # job.fail(error_msg)
                return {"error": error_msg}

        except Exception as e:
            # job.fail(str(e))
            return {"error": str(e)}
        finally:
            # Clean up temporary directory
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir)

    def _collect_output_files(self, job, result_dict):
        """
        Collect output files and add them to the results.

        Args:
            job: The job that produced the output files
            result_dict: Dictionary to update with file contents
        """
        if not job.output_files:
            return

        file_results = {}
        working_dir = job.working_dir or os.getcwd()

        for file_path in job.output_files:
            full_path = os.path.join(working_dir, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r") as f:
                        file_results[file_path] = f.read()
                except Exception as e:
                    file_results[file_path] = f"Error reading file: {str(e)}"
            else:
                file_results[file_path] = "File not found"

        if file_results:
            result_dict["output_files"] = file_results

    def run_job(self, job) -> None:
        """
        Run a job using the appropriate execution method.

        Args:
            job: The job to run
        """
        # Submit the job to our executor
        self.logger.info(f"Start to run job {job.job_id}")
        if job.job_type == JobType.FUNCTION:
            future = self.executor.submit(self._execute_function, job)
        elif job.job_type == JobType.SCRIPT:
            future = self.executor.submit(self._execute_script, job)
        elif job.job_type == JobType.CONTAINER:
            future = self.executor.submit(self._execute_container, job)
        else:
            job.fail(f"Unsupported job type: {job.job_type}")
            return

        self.running_jobs[job.job_id] = future

    def check_job_status(self, job) -> None:
        """
        Check the status of a job and update its state.

        Args:
            job: The job to check
        """
        self.logger.info(f"Check job {job.job_id} status")
        future = self.running_jobs.get(job.job_id)
        if future is None:
            return

        if future.done():
            if future.exception():
                job.fail(str(future.exception()))
            else:
                # The job should have been marked as completed in _execute_* methods
                # but we'll check just in case
                if job.state != JobState.COMPLETED:
                    job.complete(future.result())

            # Remove from running jobs
            self.running_jobs.pop(job.job_id, None)

    def cancel_job(self, job) -> None:
        """
        Cancel a job.

        Args:
            job: The job to cancel
        """
        self.logger.info(f"Cancel job {job.job_id}")
        future = self.running_jobs.get(job.job_id)
        if future and not future.done():
            future.cancel()
            job.state = JobState.CANCELLED
            self.running_jobs.pop(job.job_id, None)

    def shutdown(self):
        """
        Shutdown the executor.
        """
        self.executor.shutdown(wait=True)
