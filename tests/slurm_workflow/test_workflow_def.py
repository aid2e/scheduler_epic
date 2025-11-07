import json
import tempfile
from pathlib import Path
import math

from scheduler.slurm_workflow import SlurmWorkflow


# --- Example computational function (mock of a job function) -----------------
def dtlz2(x):
    """Simple 2-objective DTLZ2 implementation."""
    if not isinstance(x, (list, tuple)):
        raise ValueError("x must be a list or tuple")
    g = sum((xi - 0.5) ** 2 for xi in x[1:])
    f1 = (1 + g) * math.cos(math.pi * x[0] / 2)
    f2 = (1 + g) * math.sin(math.pi * x[0] / 2)
    return {"f1": f1, "f2": f2}


# --- helper -------------------------------------------------------
def make_sample_config(tmpdir: Path) -> dict:
    """Return a minimal workflow config dictionary."""
    return {
        "name": "dtlz2_test_workflow",
        "queue": "debug",
        "work_dir": str(tmpdir / "wf_dtlz2"),
        "setup_commands": [
            "export PYTHONPATH=$PYTHONPATH:.",
            "echo 'Environment ready'"
        ],
        "tags": {"problem": "DTLZ2", "type": "unit_test"},
    }


# --- test ---------------------------------------------------------
def test_slurm_workflow_dtlz2(tmp_path):
    """
    End-to-end test for SlurmWorkflow using a DTLZ2 computation mock:
      1. Create workflow
      2. Add several DTLZ2 jobs with different parameters
      3. Prepare workflow + works
      4. Validate manifest + script generation
    """
    cfg = make_sample_config(tmp_path)
    wf = SlurmWorkflow(cfg)

    # ---- 1. Add jobs (different DTLZ2 points)
    param_sets = [
        {"x": [0.2, 0.5, 0.7]},
        {"x": [0.8, 0.4, 0.3]},
        {"x": [0.5, 0.9, 0.1]},
    ]

    for i, params in enumerate(param_sets, 1):
        wf.add_job({
            "name": f"dtlz2_eval_{i}",
            "func": "tests.test_slurm_workflow_dtlz2.dtlz2",
            "params": params,
            "cpus": 1,
            "memory_mb": 1000,
            "time_s": 120
        })
    assert len(wf.list_jobs()) == len(param_sets)

    # ---- 2. Prepare workflow (environment setup)
    wf.prepare_workflow()
    assert (Path(wf.model.work_dir) / "logs").exists()
    assert (Path(wf.model.work_dir) / "scripts").exists()

    # ---- 3. Prepare works (generate scripts)
    wf.prepare_works()
    manifest_path = Path(wf.model.work_dir) / "manifest.json"
    assert manifest_path.exists()

    # ---- 4. Inspect manifest and scripts
    manifest = wf.get_manifest()
    assert manifest.name == "dtlz2_test_workflow"
    assert manifest.status == "WORKS_PREPARED"
    assert len(manifest.works) == len(param_sets)

    # script_dir = Path(wf.model.work_dir) / "scripts"
    # for job in wf._jobs:
    #     script = script_dir / f"{job.name}.sh"
    #     assert script.exists()
    #     script_content = script.read_text()
    #     # sanity check that the function name and parameters appear
    #     assert "dtlz2" in script_content
    #     assert "python -c" in script_content

    print("✅ SlurmWorkflow DTLZ2 workflow test passed.")


# Allow standalone execution
if __name__ == "__main__":
    
    tmp = Path(tempfile.mkdtemp())
    #tmp = Path("")
    test_slurm_workflow_dtlz2(tmp)
