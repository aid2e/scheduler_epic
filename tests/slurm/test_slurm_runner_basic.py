import os
import json
import tempfile
import subprocess
from pathlib import Path
import pytest

from scheduler.runners.slurm_runner import SlurmRunner
from scheduler.job import Job, JobType, JobState


# --- Fixtures --- #
@pytest.fixture
def tmp_slurm_template(tmp_path):
    """Create a temporary fake SLURM template file."""
    template_path = tmp_path / "template.slurm"
    template_path.write_text("#!/bin/bash\n#SBATCH --job-name=test_job\n")
    return template_path


@pytest.fixture
def sample_objective_function():
    """Simple DTLZ2-like function with no dependencies."""
    def objective_function(x1=0.5, x2=0.5):
        f1 = (x1 - 0.5) ** 2
        f2 = (x2 - 0.5) ** 2
        return {"f1": f1, "f2": f2}
    return objective_function


# --- Tests --- #
def test_slurm_runner_creates_script_and_wrapper(tmp_path, tmp_slurm_template, sample_objective_function, monkeypatch):
    """Test that SlurmRunner generates wrapper, user script, and submit files correctly."""

    # Create runner
    runner = SlurmRunner(slurm_template=str(tmp_slurm_template))

    # Create mock job
    job_dir = tmp_path / "job_001"
    job = Job(
        job_id="001",
        job_type=JobType.FUNCTION,
        function=sample_objective_function,
        params={"x1": 0.2, "x2": 0.8},
        working_dir=str(job_dir),
        env_vars={"TEST_ENV": "123"}
    )

    # Mock subprocess.run to avoid real sbatch execution
    def fake_run(cmd, capture_output=True, text=True):
        class Result:
            returncode = 0
            stdout = "Submitted batch job 12345"
            stderr = ""
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    # Run job
    runner.run_job(job)

    # --- Assertions --- #
    # Ensure files are created
    params_file = job_dir / "params.json"
    wrapper_file = job_dir / "function_wrapper.py"
    slurm_script = job_dir / "submit.slurm"
    output_file = job_dir / "output.json"

    assert params_file.exists(), "params.json should be created"
    assert wrapper_file.exists(), "wrapper script should be created"
    assert slurm_script.exists(), "submit.slurm should be created"

    # Validate params.json content
    with open(params_file) as f:
        params = json.load(f)
    assert params == job.params

    # Validate SLURM script contains the user command
    slurm_content = slurm_script.read_text()
    assert "python" in slurm_content
    assert "function_wrapper.py" in slurm_content
    assert "--params" in slurm_content
    assert "--output" in slurm_content
    assert "export TEST_ENV=123" in slurm_content

    # Job should be marked as running and have internal ID
    assert job.state == JobState.RUNNING
    assert job.internal_id == "12345"


def test_slurm_runner_raises_if_template_missing(tmp_path):
    """Ensure SlurmRunner raises error if template path is invalid."""
    fake_template = tmp_path / "no_template.slurm"
    with pytest.raises(FileNotFoundError):
        SlurmRunner(slurm_template=str(fake_template))
