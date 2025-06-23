"""
SlurmRunner - Runner that submits jobs to a Slurm cluster.
"""

import os
import subprocess
import pickle
import json
from typing import Dict, Any
from ..job.job import JobType
from ..job.job_state import JobState
from .base_runner import BaseRunner


class SlurmRunner(BaseRunner):
    """
    A runner that submits jobs to a Slurm cluster.

    This runner creates temporary job scripts and submits them to Slurm.
    It can handle different job types:
    - Function: Serializes and runs Python functions
    - Script: Executes scripts directly
    - Container: Runs containers using Singularity
    """

    def __init__(
        self,
        partition: str = "batch",
        time_limit: str = "01:00:00",
        memory: str = "4G",
        cpus_per_task: int = 1,
        config: Dict[str, Any] = None,
    ):
        """
        Initialize a new SlurmRunner.

        Args:
            partition: Slurm partition to submit jobs to
            time_limit: Time limit for jobs (HH:MM:SS)
            memory: Memory to allocate per job
            cpus_per_task: Number of CPUs to allocate per job
            config: Additional configuration options:
                modules: List of modules to load (default: ['python'])
                singularity_path: Path to singularity executable (default: 'singularity')
                job_dir: Directory to store job files (default: ~/slurm_jobs)
        """
        super().__init__(config or {})
        self.partition = partition
        self.time_limit = time_limit
        self.memory = memory
        self.cpus_per_task = cpus_per_task
        self.jobs = {}  # job_id -> slurm_job_id

        # Additional configuration
        self.modules = self.config.get("modules", ["python"])
        self.singularity_path = self.config.get("singularity_path", "singularity")

        # Directory to store job files
        self.job_dir = self.config.get("job_dir", os.path.expanduser("~/slurm_jobs"))
        os.makedirs(self.job_dir, exist_ok=True)

    def _create_job_script(self, job) -> str:
        """
        Create a job script for Slurm.

        Args:
            job: The job to create a script for

        Returns:
            Path to the job script
        """
        # Create a directory for this job
        job_path = os.path.join(self.job_dir, job.job_id)
        os.makedirs(job_path, exist_ok=True)

        # Create the job script
        script_path = os.path.join(job_path, "job.sh")
        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --job-name={job.job_id}\n")
            f.write(f"#SBATCH --output={job_path}/job.out\n")
            f.write(f"#SBATCH --error={job_path}/job.err\n")
            f.write(f"#SBATCH --partition={self.partition}\n")
            f.write(f"#SBATCH --time={self.time_limit}\n")
            f.write(f"#SBATCH --mem={self.memory}\n")
            f.write(f"#SBATCH --cpus-per-task={self.cpus_per_task}\n")

            # Add any additional options from config
            for k, v in self.config.get("sbatch_options", {}).items():
                f.write(f"#SBATCH --{k}={v}\n")

            f.write("\n")
            f.write("# Load modules\n")
            for module in self.modules:
                f.write(f"module load {module}\n")

            f.write("\n")
            f.write("# Set environment variables\n")
            for key, value in job.env_vars.items():
                f.write(f'export {key}="{value}"\n')

            f.write("\n")
            f.write("# Run the job\n")

            # Different job types need different handling
            if job.job_type == JobType.FUNCTION:
                # Pickle the job function and parameters
                pickle_path = os.path.join(job_path, "job.pkl")
                with open(pickle_path, "wb") as pkl_file:
                    pickle.dump((job.function, job.params), pkl_file)

                # Write Python code to execute the function
                f.write('python -c "\n')
                f.write("import pickle\n")
                f.write("import os\n")
                f.write("import sys\n")
                f.write("import json\n")
                f.write(f"with open('{pickle_path}', 'rb') as f:\n")
                f.write("    function, params = pickle.load(f)\n")
                f.write("try:\n")
                f.write("    result = function(**params)\n")
                f.write(f"    with open('{job_path}/result.json', 'w') as f:\n")
                f.write('        json.dump({"result": result}, f)\n')
                f.write("    sys.exit(0)\n")
                f.write("except Exception as e:\n")
                f.write(f"    with open('{job_path}/error.json', 'w') as f:\n")
                f.write('        json.dump({"error": str(e)}, f)\n')
                f.write("    sys.exit(1)\n")
                f.write('"\n')

            elif job.job_type == JobType.SCRIPT:
                # Create a file with the parameters
                params_file = os.path.join(job_path, "params.json")
                with open(params_file, "w") as params_f:
                    json.dump(job.params, params_f)

                # Set environment variable for the params file
                f.write(f'export JOB_PARAMS_FILE="{params_file}"\n')

                # Set working directory
                working_dir = job.working_dir if job.working_dir else job_path
                f.write(f"cd {working_dir}\n")

                # Execute the script
                if job.script_path.endswith(".sh"):
                    f.write(f"bash {job.script_path}\n")
                else:
                    f.write(f"python {job.script_path}\n")

                # Capture the exit code
                f.write("EXIT_CODE=$?\n")
                f.write("if [ $EXIT_CODE -ne 0 ]; then\n")
                f.write(f'  echo "{{\\"error\\": \\"Script exited with code $EXIT_CODE\\"}}" > {job_path}/error.json\n')
                f.write("  exit $EXIT_CODE\n")
                f.write("fi\n")

                # If no result file was created, create one with the output
                f.write(f"if [ ! -f {job_path}/result.json ]; then\n")
                f.write(f'  echo "{{\\"stdout\\": \\"$(cat {job_path}/job.out)\\"}}" > {job_path}/result.json\n')
                f.write("fi\n")

            elif job.job_type == JobType.CONTAINER:
                # Create a file with the parameters
                params_file = os.path.join(job_path, "params.json")
                with open(params_file, "w") as params_f:
                    json.dump(job.params, params_f)

                # Set environment variable for the params file
                f.write(f'export JOB_PARAMS_FILE="{params_file}"\n')

                # Execute the container using Singularity
                working_dir = job.working_dir if job.working_dir else job_path

                # Build Singularity command
                cmd = [self.singularity_path, "run"]

                # Add environment variables
                for key, value in job.env_vars.items():
                    cmd.extend(["--env", f"{key}={value}"])

                # Add bind mounts
                cmd.extend(["--bind", f"{job_path}:/job"])
                if job.working_dir:
                    cmd.extend(["--bind", f"{job.working_dir}:/workdir"])
                    cmd.extend(["--pwd", "/workdir"])
                else:
                    cmd.extend(["--pwd", "/job"])

                # Add image
                cmd.append(job.container_image)

                # Add command if specified
                if job.container_command:
                    cmd.extend(job.container_command.split())

                # Write the command to the script
                f.write(f"{' '.join(cmd)}\n")

                # Capture the exit code
                f.write("EXIT_CODE=$?\n")
                f.write("if [ $EXIT_CODE -ne 0 ]; then\n")
                f.write(f'  echo "{{\\"error\\": \\"Container exited with code $EXIT_CODE\\"}}" > {job_path}/error.json\n')
                f.write("  exit $EXIT_CODE\n")
                f.write("fi\n")

                # If no result file was created, create one with the output
                f.write(f"if [ ! -f {job_path}/result.json ]; then\n")
                f.write(f'  echo "{{\\"stdout\\": \\"$(cat {job_path}/job.out)\\"}}" > {job_path}/result.json\n')
                f.write("fi\n")

            else:
                f.write(f'echo "{{\\"error\\": \\"Unsupported job type: {job.job_type}\\"}}" > {job_path}/error.json\n')
                f.write("exit 1\n")

            # Collect output files if specified
            if job.output_files:
                f.write("\n# Collect output files\n")
                f.write(f"mkdir -p {job_path}/output_files\n")
                f.write('OUTPUT_FILES_JSON="{\\"output_files\\":{\\n')

                for i, file_path in enumerate(job.output_files):
                    src_path = os.path.join(working_dir if job.working_dir else job_path, file_path)
                    dest_path = os.path.join(job_path, "output_files", os.path.basename(file_path))

                    f.write(f'if [ -f "{src_path}" ]; then\n')
                    f.write(f'  cp "{src_path}" "{dest_path}"\n')
                    f.write(f"  FILE_CONTENT=$(cat \"{dest_path}\" | sed 's/\"/\\\\\"/g' | tr '\\n' ' ')\n")
                    f.write(f'  OUTPUT_FILES_JSON+="\\"{file_path}\\": \\"$FILE_CONTENT\\"')
                    if i < len(job.output_files) - 1:
                        f.write(",")
                    f.write('\\n"\n')
                    f.write("else\n")
                    f.write(f'  OUTPUT_FILES_JSON+="\\"{file_path}\\": \\"File not found\\"')
                    if i < len(job.output_files) - 1:
                        f.write(",")
                    f.write('\\n"\n')
                    f.write("fi\n")

                f.write('OUTPUT_FILES_JSON+="}}}"\n')

                # Merge with result.json if it exists
                f.write(f"if [ -f {job_path}/result.json ]; then\n")
                f.write("  # Combine the output files with the existing result\n")
                f.write(f"  RESULT=$(cat {job_path}/result.json)\n")
                f.write("  # Remove the closing brace\n")
                f.write("  RESULT=${RESULT%?}\n")
                f.write("  # Add a comma if the JSON isn't empty\n")
                f.write('  if [ "$RESULT" != "{" ]; then\n')
                f.write('    RESULT="$RESULT,"\n')
                f.write("  fi\n")
                f.write("  # Add the output files and closing brace\n")
                f.write("  OUTPUT_FILES_JSON=${OUTPUT_FILES_JSON#*{}\n")
                f.write('  echo "$RESULT$OUTPUT_FILES_JSON" > {job_path}/result.json\n')
                f.write("else\n")
                f.write("  # Just write the output files as the result\n")
                f.write('  echo "$OUTPUT_FILES_JSON" > {job_path}/result.json\n')
                f.write("fi\n")

        # Make the script executable
        os.chmod(script_path, 0o755)
        return script_path

    def run_job(self, job) -> None:
        """
        Submit a job to Slurm.

        Args:
            job: The job to run
        """
        job_script = self._create_job_script(job)

        # Submit the job to Slurm
        try:
            result = subprocess.run(["sbatch", job_script], capture_output=True, text=True, check=True)

            # Extract the job ID (format: "Submitted batch job 123456")
            slurm_job_id = result.stdout.strip().split()[-1]
            self.jobs[job.job_id] = slurm_job_id

            # Update job state
            job.state = JobState.RUNNING

        except subprocess.CalledProcessError as e:
            job.fail(f"Failed to submit job to Slurm: {e.stderr}")

    def check_job_status(self, job) -> None:
        """
        Check the status of a job and update its state.

        Args:
            job: The job to check
        """
        slurm_job_id = self.jobs.get(job.job_id)
        if slurm_job_id is None:
            return

        # Check if the job is still running
        try:
            result = subprocess.run(["squeue", "-j", slurm_job_id, "-h"], capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                # Job is still running or queued
                job.state = JobState.RUNNING
                return

            # Job has finished, check if it completed successfully
            job_path = os.path.join(self.job_dir, job.job_id)
            result_path = os.path.join(job_path, "result.json")
            error_path = os.path.join(job_path, "error.json")

            if os.path.exists(result_path):
                with open(result_path, "r") as f:
                    results = json.load(f)
                job.complete(results)
            elif os.path.exists(error_path):
                with open(error_path, "r") as f:
                    error = json.load(f)
                job.fail(error.get("error", "Unknown error"))
            else:
                # Check the exit code
                sacct_result = subprocess.run(
                    ["sacct", "-j", slurm_job_id, "-o", "ExitCode", "-n"],
                    capture_output=True,
                    text=True,
                )
                exit_code = sacct_result.stdout.strip().split()[0]

                if exit_code == "0:0":
                    job.complete({"result": "Job completed but no results found"})
                else:
                    job.fail(f"Job failed with exit code {exit_code}")

        except subprocess.CalledProcessError as e:
            job.fail(f"Failed to check job status: {e.stderr}")

    def cancel_job(self, job) -> None:
        """
        Cancel a job.

        Args:
            job: The job to cancel
        """
        slurm_job_id = self.jobs.get(job.job_id)
        if slurm_job_id is None:
            return

        try:
            subprocess.run(["scancel", slurm_job_id], check=True)
            job.state = JobState.CANCELLED
            self.jobs.pop(job.job_id, None)
        except subprocess.CalledProcessError:
            pass  # Job might already be completed
