# slurm_runner.py
import os
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from ..job import Job, JobType, JobState
from ..utils.common import write_function_to_file
import textwrap
import time
class SlurmRunner:
    """
    Strict Slurm Runner that only executes user-provided scripts
    using a user-supplied SLURM template.
    """

    def __init__(self, slurm_template: str,
                 init_env: Optional[list] = None,
                 source_dir: Optional[str] = None
                 ):
        """
        Initialize a new SlurmRunner.

        Args:
            slurm_template: Path to the SLURM template file to use for job submission.
            init_env: Optional list of environment setup commands to run before job execution.
            source_dir: Optional source directory to include in the job environment.

        Raises:
            FileNotFoundError: If the SLURM template file does not exist.
        """
        self.slurm_template = Path(slurm_template)
        self.logger = logging.getLogger("SlurmRunner")
        #self.logger.setLevel(logging.DEBUG)
        self.init_env = init_env or []
        self.manifest = {"jobs": [],
                         }
        if not self.slurm_template.exists():
            raise FileNotFoundError(f"SLURM template not found: {self.slurm_template}")

    def run_job(self, job: Job):
        """
        Submit a job to the Slurm cluster.

        Prepares the job environment, generates necessary scripts, and submits
        the job to Slurm using sbatch. Updates job state and internal ID upon
        successful submission.

        Args:
            job: The Job object to submit. Must have job_type of FUNCTION or SCRIPT.

        Raises:
            NotImplementedError: If job type is SCRIPT or CONTAINER (not supported).
            ValueError: If job type is unsupported.
        """
        job_dir = Path(job.working_dir) or Path.cwd() / f"job_{job.job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)
        time.sleep(0.5)  # ensure unique timestamps if many jobs created quickly
        # Write parameters to JSON (optional if script wants to read it)
        all_params = job.params.copy()
        function_additional_args = getattr(job, 'extra_args', {}).get('func_args', {})
        all_params.update(function_additional_args)
        params_file = job_dir / "params.json"
        with open(params_file, "w") as f:
            json.dump(all_params, f)
        
        if job.job_type == JobType.SCRIPT:
            job.state = JobState.FAILED
            raise NotImplementedError("Script jobs are not supported.")
        
        if job.job_type == JobType.FUNCTION:
            script_path = self._prepare_function_job(job, job_dir, params_file)
        elif job.job_type == JobType.SCRIPT:
            script_path = self._prepare_script_job(job, job_dir, params_file)
        elif job.job_type == JobType.CONTAINER:
            job.fail("Container jobs are not supported.")
            raise NotImplementedError("Container jobs are not supported.")
        else:
            job.fail(f"Unsupported job type: {job.job_type}")
            raise ValueError(f"Unsupported job type: {job.job_type}")
        
        submit_cmd = ["sbatch", str(script_path)]
        
        self.logger.info(f"Submitting SLURM job: {' '.join(submit_cmd)}")

        result = subprocess.run(submit_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            job.fail(result.stderr)
            job.state = JobState.FAILED
            self.logger.error(f"SLURM job submission failed: {result.stderr}")
            return

        slurm_id = self._parse_job_id(result.stdout)
        
        job.set_internal_id(slurm_id)
        job.state = JobState.RUNNING
        job.start_time = datetime.now()
        job.logs["stdout"] = job_dir / "slurm-{}.out".format(slurm_id)
        job.logs["stderr"] = job_dir / "slurm-{}.err".format(slurm_id)

        self.logger.info(f"Submitted job {job.job_id} with SLURM ID {slurm_id}")
    def _prepare_script_job(self, job: Job, job_dir: Path, params_file: Path) -> Path:
        """Prepare a Slurm script for a user-provided executable or script job."""
        # Check script path
        script_path = Path(job.script_path)
        if not script_path.exists():
            self.logger.error(f"Script file for objective computation not found: {script_path}")
            job.fail(f"Script file for objective computation not found: {script_path}")
            raise FileNotFoundError(f"Script file for objective computation not found: {script_path}")

        # Build SLURM script
        output_script = job_dir / "submit.slurm"
        with open(self.slurm_template, "r") as template_file:
            slurm_script = template_file.read().rstrip() + "\n\n"

        slurm_script += f"#SBATCH --job-name=job_{job.job_id}\n"
        slurm_script += f"#SBATCH --chdir={job.working_dir}\n"
        slurm_script += f"#SBATCH --output={job.working_dir}/slurm-%j.out\n"
        slurm_script += f"#SBATCH --error={job.working_dir}/slurm-%j.err\n\n"
        
        # Running on Host
        slurm_script += "# Some information about the job environment\n"
        slurm_script += 'echo "Running on host $(hostname)"\n'
        slurm_script += 'echo "Current directory: $(pwd)"\n'
        slurm_script += 'echo "SLURM Job ID: $SLURM_JOB_ID"\n\n'
        # Add initialization commands
        for cmd in self.init_env:
            slurm_script += cmd + "\n"

        # Export any environment variables
        for k, v in job.env_vars.items():
            slurm_script += f"export {k}={v}\n"

        slurm_script += f"\ncd {job.working_dir}\n"
        slurm_script += f"export TRAILID={job.job_id}\n\n"

        # --- Build the run command ---
        # e.g., "python script.py --x 0.3 --y 0.7"
        cmd_parts = [str(script_path)]
        for k, v in job.params.items():
            cmd_parts.append(f"--{k}")
            cmd_parts.append(str(v))
        cmd_str = " ".join(cmd_parts)

        slurm_script += f"# Run user script\n{cmd_str}\n"

        # Write it out
        with open(output_script, "w") as out:
            out.write(slurm_script)

        return output_script

    def _compose_slurm_script(self, job: Job, wrapper_file: Path, 
                              job_func_file: Path, function_name: str, 
                              params_file: Path, output_json_file: Path
                              ) -> Path:
        """Generate a new SLURM script from the user template."""
        output_script = Path(job.working_dir) / "submit.slurm"

        with open(self.slurm_template, "r") as template_file:
            slurm_script = template_file.read().rstrip() + "\n\n"
        # Lets define the job name 
        slurm_script += f"#SBATCH --job-name=job_{job.job_id}\n"
        # change working directory
        slurm_script += f"#SBATCH --chdir={job.working_dir}\n"
        # Lets change the output and err files to be inside job working dir
        slurm_script += f"#SBATCH --error={job.working_dir}/slurm-%j.err\n"
        slurm_script += f"#SBATCH --output={job.working_dir}/slurm-%j.out\n"
        
        slurm_script += "\n# Initial environment setup commands\n"
        for cmd in self.init_env:
            slurm_script += cmd + "\n"
        slurm_script += "\n# Environment variables\n"
        for k, v in job.env_vars.items():
            slurm_script += f"export {k}={v}\n"
        # Lets move to job working directory
        slurm_script += f"\ncd {job.working_dir}\n"
        # Lets set TrailID which is the internal job ID
        slurm_script += f"export TRAILID={job.job_id}\n"
        # Build command string
        # Example: python function_wrapper.py --file user_objective.py --function my_func --params params.json --output output.json
        cmd_parts = ["python", str(wrapper_file)]
        cmd_parts += [f"--file", str(job_func_file)]
        cmd_parts += [f"--function", function_name]
        cmd_parts += [f"--params", str(params_file)]
        cmd_parts += [f"--output", str(output_json_file)]
        cmd_str = " ".join(cmd_parts)

        slurm_script += f"# User command appended by SlurmRunner\n{cmd_str}\n"

        with open(output_script, "w") as out:
            out.write(slurm_script)

        return output_script
    def _prepare_function_job(self, job: Job, job_dir: Path, params_file: Path) -> Path:
        job_func_file = write_function_to_file(
            job.function, job_dir / f"user_objective_{job.function.__name__}.py"
        )
        output_json_file = job_dir / "result.json"
        job.output_files.append(output_json_file)

        wrapper_file = job_dir / "function_wrapper.py"
        wrapper_code = textwrap.dedent("""
        import argparse, json, importlib.util, sys
        parser = argparse.ArgumentParser()
        parser.add_argument("--file", required=True)
        parser.add_argument("--function", required=True)
        parser.add_argument("--params", required=True)
        parser.add_argument("--output", default="output.json")
        args = parser.parse_args()

        spec = importlib.util.spec_from_file_location("user_module", args.file)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["user_module"] = mod
        spec.loader.exec_module(mod)
        func = getattr(mod, args.function)

        with open(args.params) as f:
            params = json.load(f)
        result = func(**params)
        with open(args.output, "w") as f:
            json.dump(result, f)
        """)
        with open(wrapper_file, "w") as f:
            f.write(wrapper_code)

        return self._compose_slurm_script(
            job, wrapper_file, job_func_file, job.function.__name__, params_file, output_json_file
        )

    def check_job_status(self, job: Job):
        """
        Check the current status of a submitted job.

        Queries the Slurm scheduler to determine if the job is pending, running,
        or completed. Updates the job state and collects results if the job
        has finished execution.

        Args:
            job: The Job object whose status should be checked.
        """
        if not job.internal_id:
            return

        result = subprocess.run(
            ["squeue", "--noheader", "--job", str(job.internal_id)],
            capture_output=True,
            text=True
        )
        self.logger.debug(f"Checking status of SLURM job ID {job.internal_id}")
        if result.returncode != 0 or not result.stdout.strip():
            # Job disappeared from queue — assume done
            self._collect_results(job, )
        else:
            job.state = JobState.RUNNING

    def _collect_results(self, job: Job, outputPath: Optional[Path] = None):
        output_file = job.output_files[0]

        if not output_file.exists():
            job.fail(f"Missing result.json after SLURM job completion at {output_file}")
            return

        with open(output_file, "r") as f:
            job.complete(json.load(f)) # updates and sets the results of the job
        job.endtime = datetime.now()

    def cancel_job(self, job: Job):
        """
        Cancel a job that has been submitted to Slurm.

        Sends a signal to the Slurm scheduler to terminate the job and updates
        the job state to CANCELLED.

        Args:
            job: The Job object to cancel.
        """
        if job.internal_id:
            subprocess.run(["scancel", str(job.internal_id)])
            job.state = JobState.CANCELLED

    def _parse_job_id(self, sbatch_output: str) -> Optional[str]:
        try:
            return sbatch_output.strip().split()[-1]
        except Exception:
            return None
