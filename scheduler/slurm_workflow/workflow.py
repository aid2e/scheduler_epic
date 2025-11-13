# slurm_workflow/workflow.py

from __future__ import annotations

import json, shutil
import logging
from pathlib import Path
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from pydantic import ValidationError
from enum import Enum, auto
from .models import SlurmWorkflowModel, SlurmWorkModel


JsonDict = Dict[str, Any]
ConfigInput = Union[str, Path, Dict[str, Any], SlurmWorkflowModel]

class SlurmWorkflowStatus(str, Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()

class SlurmWorkflow:
    """
    Runtime manager for a Slurm workflow.

    - Wraps a validated SlurmWorkflowModel (metadata/config only)
    - Lets you add SlurmWorkModel jobs dynamically
    - Creates and updates a manifest.json file under work_dir
    - Provides helpers to track status, list jobs, register submission IDs, etc.
    """

    def __init__(self, config: ConfigInput, *, auto_init_manifest: bool = True) -> None:
        # Load/validate workflow model
        if isinstance(config, SlurmWorkflowModel):
            self.model: SlurmWorkflowModel = config
        elif isinstance(config, (str, Path)):
            self.model = self._load_from_yaml(Path(config))
        elif isinstance(config, dict):
            self.model = SlurmWorkflowModel(**config)
        else:
            raise TypeError("config must be a SlurmWorkflowModel, a dict, or a YAML file path")

        # Internal state
        self.log = logging.getLogger(self.__class__.__name__)
        self.work_dir = Path(self.model.work_dir)
        # Create work_dir if missing
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.work_dir / "manifest.json"

        # Jobs tracked in memory (authoritative copy is the manifest)
        self._jobs: List[SlurmWorkModel] = [] if not self.model.works else self.model.works
        
        if auto_init_manifest:
            self._ensure_manifest_initialized()

    # -------------------------------------------------------------------------
    # Initialization helpers
    # -------------------------------------------------------------------------
    def _load_from_yaml(self, yaml_path: Path) -> SlurmWorkflowModel:
        if not yaml_path.exists():
            raise FileNotFoundError(f"Workflow YAML not found: {yaml_path}")
        with yaml_path.open("r") as f:
            data = yaml.safe_load(f) or {}
        try:
            return SlurmWorkflowModel(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid workflow YAML ({yaml_path}): {e}") from e

    # -------------------------------------------------------------------------
    # Workflow Preparation
    # -------------------------------------------------------------------------
    def prepare_workflow(self) -> None:
        """
        Prepare the global workflow environment.

        Tasks:
          - Create workflow directory structure (scripts/, logs/)
          - Clean old log/output files if needed
          - Validate Slurm command availability (sbatch, squeue, scancel)
          - Initialize manifest.json if missing
        """
        self.log.info("[SlurmWorkflow] Preparing workflow environment")

        # Ensure base directories exist
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Clean up old logs (optional but tidy)
        for ext in ("*.out", "*.err"):
            for f in self.work_dir.glob(ext):
                f.unlink(missing_ok=True)

        # Verify Slurm commands are available
        for cmd in ["sbatch", "squeue", "scancel"]:
            if not shutil.which(cmd):
                raise EnvironmentError(f"Required Slurm command '{cmd}' not found in PATH")

        # Initialize manifest if it doesn't exist
        if not self.manifest_path.exists():
            self._ensure_manifest_initialized()

        self.model.status = "WORKFLOW_PREPARED"
        self.write_manifest()
        self.log.info("[SlurmWorkflow] Workflow directories and manifest ready.")


    # -------------------------------------------------------------------------
    # Manifest management (full + incremental)
    # -------------------------------------------------------------------------
    def _ensure_manifest_initialized(self) -> None:
        """
        Create a minimal manifest if one doesn't exist, else load jobs from it.
        """
        if self.manifest_path.exists():
            # Load existing manifest and hydrate self._jobs
            manifest = self.get_manifest()
            self._hydrate_jobs_from_manifest(manifest)
            # ensure model.manifest_path is set
            self.model.manifest_path = str(self.manifest_path)
            return
        
        self._atomic_write_json(self.model, self.manifest_path)
        self.model.manifest_path = str(self.manifest_path)

    def write_manifest(self) -> None:
        """
        Write the current complete state (workflow + all jobs) to manifest.json.
        Use this to emit a full snapshot (idempotent).
        """
        self.model.updated_at = datetime.now(UTC).isoformat()
        self._atomic_write_json(self.model, self.manifest_path)

    def update_manifest_for_job(self, internal_id: str) -> None:
        """
        Update/insert a single job entry in manifest.json (incremental safe update).
        """
        job = self.get_job(internal_id)
        if job is None:
            raise ValueError(f"No job with internal_id={internal_id} to update manifest")

        manifest = self.model
        # replace or append
        for idx, w in enumerate(manifest.works):
            if w.internal_id == internal_id:
                manifest.works[idx] = job
                break
        else:
            manifest.works.append(job)
        manifest.updated_at = datetime.now(UTC).isoformat()
        self._atomic_write_json(self.model, self.manifest_path)

    def get_manifest(self) -> SlurmWorkflowModel:
        """Return current manifest JSON as a dict."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")
        with self.manifest_path.open("r") as f:
            return self._load_from_yaml(self.manifest_path)

    def _hydrate_jobs_from_manifest(self, manifest: SlurmWorkflowModel) -> None:
        """Populate self._jobs from an on-disk manifest (used on init)."""
        self._jobs.clear()
        for w in manifest.works:
            try:
                w = w.model_dump()
                self._jobs.append(SlurmWorkModel(**w))
            except ValidationError as e:
                self.log.warning("Skipping invalid work in manifest: %s", e)

    @staticmethod
    def _atomic_write_json(model: SlurmWorkflowModel, path: Path) -> None:
        tmp = path.with_suffix(".json.tmp")
        with tmp.open("w") as f:
            f.write(model.model_dump_json(indent=4))
        tmp.replace(path)

    # -------------------------------------------------------------------------
    # Job management
    # -------------------------------------------------------------------------
    def add_job(self, job: Union[SlurmWorkModel, Dict[str, Any]]) -> SlurmWorkModel:
        """
        Add a job to the workflow and update manifest incrementally.

        If a dict is provided, it is validated into SlurmWorkModel.
        Applies no implicit merging of setup_commands; that's handled later when generating scripts.
        """
        job_model = job if isinstance(job, SlurmWorkModel) else SlurmWorkModel(**job)

        # Ensure internal_id uniqueness in memory:
        if any(j.internal_id == job_model.internal_id for j in self._jobs):
            raise ValueError(f"Duplicate job internal_id detected: {job_model.internal_id}")

        self._jobs.append(job_model)
        self.update_manifest_for_job(job_model.internal_id)
        self.log.info("Added job '%s' (internal_id=%s)", job_model.name, job_model.internal_id)
        return job_model

    def list_jobs(self) -> List[Tuple[str, str, str]]:
        """Return (name, state, internal_id) for quick inspection."""
        return [(j.name, j.state, j.internal_id) for j in self._jobs]

    def get_job(self, internal_id: str) -> Optional[SlurmWorkModel]:
        """Fetch a job by internal_id (None if not found)."""
        for j in self._jobs:
            if j.internal_id == internal_id:
                return j
        return None
    def get_jobs_status(self) -> Dict[str, str]:
        """Return a mapping of internal_id to job state for all jobs."""
        return {j.internal_id: j.state for j in self._jobs}

    def remove_job(self, internal_id: str) -> bool:
        """Remove a job from memory and manifest. Returns True if removed."""
        idx = next((i for i, j in enumerate(self._jobs) if j.internal_id == internal_id), None)
        if idx is None:
            return False
        self._jobs.pop(idx)
        self.model.works.pop(idx)
        self.model.updated_at = datetime.now(UTC).isoformat()
        self._atomic_write_json(self.model, self.manifest_path)
        return True

    # -------------------------------------------------------------------------
    # Status + bookkeeping helpers
    # -------------------------------------------------------------------------
    def set_status(self, status: str) -> None:
        """Update workflow status and write full manifest snapshot."""
        self.model.status = status
        self.write_manifest()
        self.log.info("Workflow status -> %s", status)

    def update_job_state(self, internal_id: str, state: str) -> None:
        """Update a job's state (e.g., PENDING/RUNNING/SUBMITTED/COMPLETED/FAILED) and persist."""
        job = self.get_job(internal_id)
        if job is None:
            raise ValueError(f"No job with internal_id={internal_id}")
        job.state = state
        self.update_manifest_for_job(internal_id)

    def register_submission_id(self, internal_id: str, slurm_job_id: str) -> None:
        """
        Record the Slurm job ID for a job and persist in both the job entry and
        the workflow's slurm_submission_ids map.
        """
        job = self.get_job(internal_id)
        if job is None:
            raise ValueError(f"No job with internal_id={internal_id}")

        job.slurm_job_id = slurm_job_id
        self.model.slurm_submission_ids[internal_id] = slurm_job_id
        # Persist both job update and workflow map change
        self.update_manifest_for_job(internal_id)
        self.write_manifest()

    # -------------------------------------------------------------------------
    # Setup command resolution
    # -------------------------------------------------------------------------
    def get_effective_setup_commands(self, job: SlurmWorkModel) -> Optional[List[str]]:
        """
        Resolve the shell setup commands for a job:
        - If the job defines setup_commands, use those.
        - Else fall back to the workflow-level setup_commands.
        """
        if job.setup_commands and len(job.setup_commands) > 0:
            return job.setup_commands
        return self.model.setup_commands

    # -------------------------------------------------------------------------
    # Export helpers (optional quality-of-life)
    # -------------------------------------------------------------------------
    def export_workflow_yaml(self, path: Union[str, Path]) -> None:
        """
        Dump the *workflow model only* (no jobs) to YAML for portability.
        """
        p = Path(path)
        payload = self.model.model_dump(exclude_none=True)
        with p.open("w") as f:
            yaml.safe_dump(payload, f, sort_keys=False)

    def reload_from_manifest(self) -> None:
        """
        Re-sync in-memory model fields that might have changed and rehydrate jobs
        from the current on-disk manifest. (Useful if another process updated it.)
        """
        manifest = self.get_manifest()

        self._hydrate_jobs_from_manifest(manifest)

    # Lets users prepare all jobs for execution
    def prepare_works(self) -> None:
        """
        Prepare all jobs for execution:
        - Validate job definitions
        - Generate Slurm scripts
        - Update manifest.json
        """
        self.log.info("[SlurmWorkflow] Preparing jobs for submission")
        for job in self._jobs:
            # Enter the logic here
            script_path = ""  # Placeholder for actual script generation logic
            # job.prepare(args....add())
            self.log.info("Generated script for job %s: %s", job.name, script_path)
            self.update_manifest_for_job(job.internal_id)

        self.model.status = "WORKS_PREPARED"
        self.write_manifest()
    
    def run_works(self) -> None:
        """
        Submit all prepared jobs to Slurm.
        """
        self.log.info("[SlurmWorkflow] Submitting jobs to Slurm")
        for job in self._jobs:
            # Enter the logic here
            #slurm_job_id = job.submit(job) 
            self.register_submission_id(job.internal_id, slurm_job_id)
            self.log.info("Submitted job %s with Slurm ID %s", job.name, slurm_job_id)

        self.model.status = "WORKS_SUBMITTED"
        self.write_manifest()

    def get_output(self) -> Dict[str, Any]:
        """
        Return the workflow's final output dictionary.

        Behavior:
          - Only returns if workflow.status == 'COMPLETED'
          - Reads JSON from the output path specified in model.output['path']
          - Validates that required keys exist (if provided)
        """
        if self.model.status != "COMPLETED":
            raise RuntimeError(f"Workflow '{self.model.name}' not complete (status={self.model.status})")

        output_spec = self.model.output
        if not output_spec or "path" not in output_spec:
            raise ValueError("Output path not defined in workflow model.")

        output_path = Path(output_spec["path"])
        if not output_path.exists():
            raise FileNotFoundError(f"Output file not found: {output_path}")

        with open(output_path, "r") as f:
            data = json.load(f)

        expected_keys = output_spec.get("keys")
        if expected_keys:
            missing = [k for k in expected_keys if k not in data]
            if missing:
                raise ValueError(f"Missing expected output keys: {missing}")

        return data


class SlurmWork:
    """
    Runtime manager for a Slurm work (job).
    Wraps a SlurmWorkModel and provides helpers for script generation,
    submission, status tracking, and output retrieval.
    """

    def __init__(self, model: SlurmWorkModel, workflow: SlurmWorkflow) -> None:
        self.model = model
        self.workflow = workflow
        self.log = logging.getLogger(f"SlurmWork[{self.model.internal_id}]")

    # Further methods for preparing, submitting, tracking, and retrieving output
    # would be implemented here.