# slurm_runner.py
import os
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from ..job import Job, JobType, JobState

class SlurmRunner:
    """
    Strict Slurm Runner that only executes user-provided scripts
    using a user-supplied SLURM template.
    """

    def __init__(self, slurm_template: str, base_dir: str = "slurm_jobs"):
        self.base_dir = Path(base_dir)
        self.slurm_template = Path(slurm_template)
        self.logger = logging.getLogger("SlurmRunner")

        if not self.slurm_template.exists():
            raise FileNotFoundError(f"SLURM template not found: {self.slurm_template}")

        self.base_dir.mkdir(parents=True, exist_ok=True)

    def run_job(self, job: Job):
        if job.job_type != JobType.SCRIPT:
            raise ValueError("SlurmRunner only supports SCRIPT job types")

        job_dir = self.base_dir / f"job_{job.job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)

        # Write parameters to JSON (optional if script wants to read it)
        params_file = job_dir / "params.json"
        with open(params_file, "w") as f:
            json.dump(job.params, f)

        # Write the slurm job script by appending user’s command to the template
        script_path = self._compose_slurm_script(job, job_dir, params_file)

        submit_cmd = ["sbatch", str(script_path)]
        self.logger.info(f"Submitting SLURM job: {' '.join(submit_cmd)}")

        result = subprocess.run(submit_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            job.fail(result.stderr)
            return

        slurm_id = self._parse_job_id(result.stdout)
        job.set_internal_id(slurm_id)
        job.state = JobState.RUNNING
        job.start_time = datetime.now()

        self.logger.info(f"Submitted job {job.job_id} with SLURM ID {slurm_id}")

    def _compose_slurm_script(self, job: Job, job_dir: Path, params_file: Path) -> Path:
        """Generate a new SLURM script from the user template."""
        output_script = job_dir / "submit.slurm"

        with open(self.slurm_template, "r") as template_file:
            slurm_script = template_file.read().rstrip() + "\n\n"

        # Build command string
        # Example: python myscript.py --x 0.2 --y 0.4
        cmd_parts = [job.script_path]
        for k, v in job.params.items():
            cmd_parts += [f"--{k}", str(v)]
        cmd_str = " ".join(cmd_parts)

        slurm_script += f"# User command appended by SlurmRunner\n{cmd_str}\n"

        with open(output_script, "w") as out:
            out.write(slurm_script)

        return output_script

    def check_job_status(self, job: Job):
        if not job.internal_id:
            return

        result = subprocess.run(
            ["squeue", "--noheader", "--job", str(job.internal_id)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0 or not result.stdout.strip():
            # Job disappeared from queue — assume done
            self._collect_results(job)
        else:
            job.state = JobState.RUNNING

    def _collect_results(self, job: Job):
        job_dir = self.base_dir / f"job_{job.job_id}"
        output_file = job_dir / "output.json"

        if not output_file.exists():
            job.fail("Missing output.json after SLURM job completion")
            return

        with open(output_file, "r") as f:
            job.complete(json.load(f))

    def cancel_job(self, job: Job):
        if job.internal_id:
            subprocess.run(["scancel", str(job.internal_id)])
            job.state = JobState.CANCELLED

    def _parse_job_id(self, sbatch_output: str) -> Optional[str]:
        try:
            return sbatch_output.strip().split()[-1]
        except Exception:
            return None
