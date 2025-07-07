from pydantic import BaseModel
from typing import Optional
import yaml

from TrackerOptimization.configurations.problem_config import ProblemConfiguration
from TrackerOptimization.configurations.optimization_config import OptimizationConfiguration


class FullConfig(BaseModel):
    """
    Top-level configuration that encapsulates the full workflow.
    """
    problem_configuration: ProblemConfiguration
    optimization_configuration: Optional[OptimizationConfiguration] = None


def load_config(yaml_path: str) -> FullConfig:
    """
    Load the holistic optimization configuration from a YAML file.

    Args:
        yaml_path (str): Path to the YAML configuration file.

    Returns:
        FullConfig: Parsed and validated configuration object.
    """
    with open(yaml_path, 'r') as file:
        config_data = yaml.safe_load(file)
    return FullConfig(**config_data)
