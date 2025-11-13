import os
import json
import time
import subprocess
from pathlib import Path
import pytest

from scheduler.runners.slurm_runner import SlurmRunner
from scheduler.job import Job, JobType, JobState


@pytest.mark.integration
def test_slurm_runner_real_submission(tmp_path):
    """
    This test actually submits a SLURM job, runs the wrapper + user function,
    waits for completion, and checks that output.json is produced.
    """

    # --- Setup ----------------------------------------------------------------
    slurm_template = tmp_path / "template.slurm"
    slurm_template.write_text(
        "#!/bin/bash\n"
        "#SBATCH --job-name=slurm_test\n"
        "#SBATCH --time=00:01:00\n"
        "#SBATCH --ntasks=1\n"
        "#SBATCH --error=slurm-%j.err\n"
        "#SBATCH --output=slurm-%j.out\n"
    )

    # Define a simple objective function that runs instantly
    def objective_function(num_objs=2, **params):
        import numpy as np

        def dtlz2(X, m=2):
            X = np.asarray(X, dtype=np.float64)
            n_points, d = X.shape
            k = d - m + 1
            g = np.sum((X[:, -k:] - 0.5) ** 2, axis=1)
            f = np.ones((n_points, m)) * (1 + g[:, np.newaxis])
            for i in range(m):
                for j in range(m - i - 1):
                    f[:, i] *= np.cos(0.5 * np.pi * X[:, j])
                if i > 0:
                    f[:, i] *= np.sin(0.5 * np.pi * X[:, m - i - 1])
            return f / np.linalg.norm(f, axis=1, keepdims=True)

        x = [params[f"x{i}"] for i in range(len(params))]
        x_array = np.array([x])
        f = dtlz2(x_array, m=num_objs)[0]
        return {f"f{i+1}": (float(f[i]), 0.0) for i in range(num_objs)}

    init_env = ["module load miniforge3/24.9.2-0", "conda activate env_AID2EHol"]
    runner = SlurmRunner(slurm_template=str(slurm_template), init_env=init_env)

    job_dir = tmp_path / "real_slurm_job"
    job = Job(
        job_id="real001",
        job_type=JobType.FUNCTION,
        function=objective_function,
        params={"x0": 0.2, "x1": 0.8},
        working_dir=str(job_dir),
        env_vars={},
        extra_args={"func_args": {"num_objs": 2}}
    )

    # --- Submit job ------------------------------------------------------------
    runner.run_job(job)
    assert job.internal_id is not None, "SLURM job ID not detected"
    print(f"Submitted SLURM job ID: {job.internal_id}")

    # --- Poll for job completion -----------------------------------------------
    timeout = 60  # seconds
    poll_interval = 5
    elapsed = 0

    while elapsed < timeout:
        result = subprocess.run(
            ["squeue", "--noheader", "--job", str(job.internal_id)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0 or not result.stdout.strip():
            break  # job finished
        time.sleep(poll_interval)
        elapsed += poll_interval
        print(f"Waiting for job {job.internal_id}...")

    # --- Verify output ---------------------------------------------------------
    output_json = job_dir / "output.json"

    # Give filesystem some buffer time
    time.sleep(2)

    assert output_json.exists(), f"Expected output.json not found in {job_dir}"

    with open(output_json) as f:
        data = json.load(f)

    print("Output.json contents:", data)
    
    # --- Cleanup ---------------------------------------------------------------
    subprocess.run(["scancel", str(job.internal_id)], check=False)
    print(f"Cancelled job {job.internal_id} (if still running)")
