from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class SlurmWorkModel(BaseModel):
    """
    Represents a single Slurm job ("work") definition within a workflow.
    """

    name: str = Field(..., description="Unique name for this work/job.")
    func: str = Field(..., description="Fully qualified function path (e.g. module.function).")
    params: Dict[str, Any] = Field(default_factory=dict, description="Function parameters.")
    workflow_id: Optional[str] = Field(None, description="ID of the parent workflow.")
    cpus: int = Field(default=1, ge=1, description="Number of CPU cores per job.")
    memory_mb: int = Field(default=4000, ge=100, description="Memory per job (in MB).")
    time_s: int = Field(default=3600, ge=60, description="Walltime in seconds.")
    output_file: Optional[str] = Field(None, description="Output file name for this work.")
    state: str = Field(default="PENDING", description="Current job state.")
    internal_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique internal job ID.")
    slurm_job_id: Optional[str] = Field(None, description="Actual Slurm job ID (after submission).")
    depends_on: Optional[List[str]] = Field(None, description="List of internal_ids this job depends on.")
    setup_commands: Optional[List[str]] = Field(
        default=None,
        description="List of shell commands to set up this job's environment (e.g., module load, source, export)."
    )
    tags: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for filtering or grouping.")



class SlurmWorkflowModel(BaseModel):
    """
    Declarative metadata model for a Slurm workflow.
    This defines workflow identity, configuration, and runtime tracking info,
    but does NOT directly hold the works (jobs) themselves.
    """

    # --- Identification ---
    workflow_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique workflow ID (UUID or derived from Ax trial)."
    )
    name: str = Field(..., description="Human-readable workflow name.")
    trial_id: Optional[int] = Field(None, description="Link to Ax or optimizer trial ID (if applicable).")

    # --- Metadata ---
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the workflow was created."
    )
    created_by: Optional[str] = Field(None, description="Name or system that created this workflow.")
    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp when the workflow was last updated."
    )
    version: str = Field(default="1.0", description="Workflow schema version.")

    # --- Execution context ---
    queue: str = Field(default="default", description="Target Slurm queue or partition.")
    work_dir: str = Field(..., description="Base directory for workflow artifacts (scripts, logs, manifest, etc.).")
    setup_commands: Optional[List[str]] = Field(
        default=None,
        description="List of shell commands to set up global environment (e.g., module load, source, export)."
    )
    # ---- new output spec ----
    output: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Specification of workflow output. "
            "Must include 'path' (absolute or relative path to output.json) "
            "and optionally 'keys' (list of expected dictionary keys)."
        ),
    )

    # --- Runtime and tracking ---
    manifest_path: Optional[str] = Field(
        None,
        description="Path to workflow manifest JSON file generated after preparation."
    )
    # Make an optional works list to hold SlurmWorkModel references
    works: Optional[List[SlurmWorkModel]] = Field(
        default=[],
        description="List of works (jobs) associated with this workflow."
    )
    status: str = Field(
        default="PENDING",
        description="Current workflow state (PENDING, PREPARED, SUBMITTED, COMPLETED, FAILED, etc.)."
    )
    slurm_submission_ids: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of internal work IDs to their submitted Slurm job IDs."
    )
    tags: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata for tagging, provenance, or grouping workflows."
    )

    # --- Validators ---
    @field_validator("setup_commands")
    def normalize_setup_commands(cls, cmds):
        """
        Ensure setup_commands is always a list of strings.
        """
        if cmds is None:
            return None
        if isinstance(cmds, str):
            # Allow a single command as string input
            return [cmds]
        if not all(isinstance(c, str) for c in cmds):
            raise ValueError("All setup commands must be strings.")
        return cmds

    @field_validator("output")
    def validate_output(cls, v):
        """
        Validate the output specification for a Slurm workflow model.

        Ensures that if an output specification is provided, it contains a 'path' key
        and that 'keys' (if present) is a list or tuple of strings.

        Args:
            v: The output specification dictionary to validate.

        Returns:
            The validated output specification.

        Raises:
            ValueError: If output spec is missing 'path', 'path' is not a string,
                or 'keys' is not a list/tuple.
        """
        if v is None:
            return v
        if "path" not in v:
            raise ValueError("Output spec must include a 'path' key.")
        if not isinstance(v["path"], str):
            raise ValueError("Output 'path' must be a string.")
        if "keys" in v and not isinstance(v["keys"], (list, tuple)):
            raise ValueError("Output 'keys' must be a list or tuple of strings.")
        return v