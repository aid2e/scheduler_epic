from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field

from .base_models import ContainerConfig


class JobInputConfig(BaseModel):
    """
    Defines the inputs required by a job. Currently supports only the design config file.
    """
    design_config: str


class JobScriptConfig(BaseModel):
    """
    Optional user-provided script paths for the job.
    """
    check_overlaps: Optional[str] = ""
    validate_geometry: Optional[str] = ""
    test_loading: Optional[str] = ""


class JobCommandConfig(BaseModel):
    """
    Specifies the execution commands for the job. Can be user-defined or defaulted.
    """
    setup: Union[str, None] = "default"
    execute: Union[str, None] = "default"
    validation: Union[str, None] = "default"


class JobDefinition(BaseModel):
    """
    A single job within a workflow.
    """
    type: str
    depends_on: List[str] = Field(default_factory=list)
    parallel: bool = False
    inputs: JobInputConfig
    scripts: Optional[JobScriptConfig] = None
    commands: Optional[JobCommandConfig] = None


class WorkflowConfig(BaseModel):
    """
    Defines a complete workflow, including its jobs and container settings.
    """
    name: str
    description: Optional[str] = ""
    execution_system: Optional[str]  # e.g., "slurm"
    container: Optional[ContainerConfig] = None
    jobs: Dict[str, JobDefinition]


class MetricsConfiguration(BaseModel):
    """
    Wrapper for the metrics definition, which currently embeds a full workflow.
    """
    type: str  # e.g., "combined"
    workflow: WorkflowConfig
