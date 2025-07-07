from typing import Optional
from pydantic import BaseModel


class OptimizerConfig(BaseModel):
    """
    Configuration for the optimizer backend. Points to the optimizer's settings file.
    """
    file: str


class OptimizationConfiguration(BaseModel):
    """
    Top-level configuration block for optimization setup.
    """
    name: str
    description: Optional[str] = ""
    optimizer: str  # e.g., "MOBO"
    optimizer_config: OptimizerConfig
