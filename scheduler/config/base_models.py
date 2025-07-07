from typing import Dict, List, Optional, Tuple, Union, Literal
from pydantic import BaseModel, Field

# Base class for all design parameters
class BaseParameter(BaseModel):
    name: str
    type: str  # Discriminator

class RangeParameter(BaseParameter):
    value: float
    bounds: Tuple[float, float]

    @property
    def type(self) -> Literal["range"]:
        return "range"

class ChoiceParameter(BaseParameter):
    value: str
    choices: List[str]

    @property
    def type(self) -> Literal["choice"]:
        return "choice"

# Unified parameter type
Parameter = Union[RangeParameter, ChoiceParameter]


def parse_parameter(name: str, data: dict) -> Parameter:
    """
    Parses a raw dictionary into a Parameter object (RangeParameter or ChoiceParameter).
    Automatically injects the name into the data.
    """
    data["name"] = name

    if "bounds" in data:
        try:
            return RangeParameter(**data)
        except Exception as e:
            raise ValueError(f"Invalid range parameter '{name}': {e}")

    if "choices" in data:
        if not isinstance(data.get("value"), str):
            raise ValueError(
                f"Parameter '{name}' appears to be a choice parameter, but its value `{data.get('value')}` is not a string. "
                f'Wrap it in quotes: value: "{data.get("value")}"'
            )
        try:
            return ChoiceParameter(**data)
        except Exception as e:
            raise ValueError(f"Invalid choice parameter '{name}': {e}")

    raise ValueError(
        f"Parameter '{name}' must have either 'bounds' (for range) or 'choices' (for choice)."
    )

class ContainerConfig(BaseModel):
    bind_paths: List[str] = Field(default_factory=list)
    environment_vars: Dict[str, str] = Field(default_factory=dict)