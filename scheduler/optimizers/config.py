from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Type

class OptimizerConfig(BaseModel):
    """Base optimizer configuration."""
    name: str
    type: str
    max_iterations: int = Field(default=100, ge=1)
    convergence_threshold: float = Field(default=1e-6, gt=0)
    

class BayesianOptimizerConfig(OptimizerConfig):
    """Bayesian optimizer configuration."""
    type: str = "bayesian"
    acquisition_function: str = Field(default="expected_improvement")
    n_initial_points: int = Field(default=10, ge=1)

class GeneticOptimizerConfig(OptimizerConfig):
    """Genetic algorithm optimizer configuration."""
    type: str = "genetic"
    population_size: int = Field(default=50, ge=2)
    mutation_rate: float = Field(default=0.1, ge=0, le=1)

# Registry within the module
OPTIMIZER_CONFIGS: Dict[str, Type[OptimizerConfig]] = {
    "ax": BayesianOptimizerConfig,
    "genetic": GeneticOptimizerConfig,
}

def get_optimizer_config(config_type: str) -> Type[OptimizerConfig]:
    """Get optimizer configuration class by type."""
    if config_type not in OPTIMIZER_CONFIGS:
        raise ValueError(f"Unknown optimizer type: {config_type}. Available: {list(OPTIMIZER_CONFIGS.keys())}")
    return OPTIMIZER_CONFIGS[config_type]

def create_optimizer_config(config_dict: Dict[str, Any]) -> OptimizerConfig:
    """Create and validate optimizer configuration."""
    config_type = config_dict.get("type")
    config_class = get_optimizer_config(config_type)
    return config_class(**config_dict)