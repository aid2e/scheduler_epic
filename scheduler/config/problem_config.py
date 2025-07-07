from typing import Optional, List
from pydantic import BaseModel, model_validator
from pathlib import Path
import os

from .enums import ProblemType
from .design_config import DesignConfigWrapper
from .workflow_config import MetricsConfiguration


class EpicConfiguration(BaseModel):
    singularity_image: str
    epic_install: Optional[str] = None
    eic_recon_install: Optional[str] = None
    eic_shell: Optional[str] = None
    eic_recon: Optional[str] = None

    def activate(self):
        # Set defaults if not provided
        if self.epic_install:
            os.environ["EPIC_INSTALL"] = self.epic_install
            if not self.eic_recon_install:
                self.eic_recon_install = str(Path(self.epic_install) / "local")
        if self.eic_recon_install:
            os.environ["EIC_RECON_INSTALL"] = self.eic_recon_install
        if self.singularity_image:
            os.environ["EIC_SHELL"] = self.singularity_image
        if self.eic_recon:
            os.environ["EIC_RECON"] = self.eic_recon

        print("[INFO] ePIC environment variables set:")
        for var in ["EPIC_INSTALL", "EIC_RECON_INSTALL", "EIC_SHELL", "EIC_RECON"]:
            if var in os.environ:
                print(f"  {var} = {os.environ[var]}")



class ProblemConfiguration(BaseModel):
    name: str
    output_location: str
    work_location: str
    problem_type: ProblemType
    design_config: DesignConfigWrapper
    epic_configuration: Optional[EpicConfiguration] = None
    metrics_configuration: MetricsConfiguration

    def _validate_paths_and_types(self):
        errors: List[str] = []

        # Check directory paths
        for label, path in [("output_location", self.output_location),
                            ("work_location", self.work_location)]:
            if not Path(path).exists():
                errors.append(f"{label} does not exist: {path}")

        # Check design config is valid
        try:
            _ = self.design_config.get()
        except Exception as e:
            errors.append(f"Invalid design config: {e}")

        # Container bind paths
        container = self.metrics_configuration.workflow.container
        if container:
            for bind_path in container.bind_paths:
                if bind_path and not Path(bind_path).exists():
                    errors.append(f"Bind path does not exist: {bind_path}")

        # ePIC installation files
        if self.epic_configuration:
            if not Path(self.epic_configuration.epic_install).exists():
                errors.append(f"epic_install path does not exist: {self.epic_configuration.epic_install}")
            if not Path(self.epic_configuration.singularity_image).exists():
                errors.append(f"Singularity image path does not exist: {self.epic_configuration.singularity_image}")

        if errors:
            raise ValueError("ProblemConfiguration validation failed:\n" + "\n".join(errors))

    @model_validator(mode="after")
    def validate_after_init(self) -> "ProblemConfiguration":
        self._validate_paths_and_types()
        # Check if its epic_configuration is set and activate it
        if self.epic_configuration:
            self.epic_configuration.activate()
        return self
