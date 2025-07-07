from typing import Dict, List, Optional
from pydantic import BaseModel, Field, RootModel, model_validator, PrivateAttr
from pathlib import Path
import yaml, os, re

from .base_models import Parameter, BaseParameter


class ParameterGroup(BaseModel):
    parameters: Dict[str, Parameter]


class ParameterConstraint(BaseModel):
    name: str
    description: Optional[str] = ""
    rule: str

class DesignParameters(RootModel[Dict[str, ParameterGroup]]):

    @model_validator(mode="before")
    @classmethod
    def inject_qualified_names(cls, values: Dict[str, dict]):
        """
        Injects full qualified names like group.param into each parameter.
        """
        for group_name, group_data in values.items():
            param_dict = group_data.get("parameters", {})
            for param_name, param in param_dict.items():
                if isinstance(param, dict) and "name" not in param:
                    param["name"] = f"{group_name}.{param_name}"
        return values


class DesignConfig(BaseModel):
    design_parameters: DesignParameters
    parameter_constraints: Optional[List[ParameterConstraint]] = Field(default_factory=list)
    
    _constraints_validated: bool = PrivateAttr(default=False)

    def get_flat_parameters(self) -> Dict[str, BaseParameter]:
        """
        Returns a flat dictionary of all parameters keyed by their qualified name.
        """
        flat = {}
        for group in self.design_parameters.root.values():
            for param in group.parameters.values():
                flat[param.name] = param
        return flat

    def expand_constraints(self) -> List[ParameterConstraint]:
        """
        TODO: Implement wildcard-based constraint expansion.
        """
        raise NotImplementedError("expand_constraints() is not implemented yet.")

    def validate_parameter_constraints_declaration(self):
        """
        Validates that all variables used in constraints are declared parameters.
        Raises ValueError if any undefined variables are found.
        """
        if not self.parameter_constraints:
            self._constraints_validated = True
            return

        known_params = set(self.get_flat_parameters().keys())

        for constraint in self.parameter_constraints:
            used_vars = self._extract_constraint_variables(constraint.rule)
            undefined = [v for v in used_vars if v not in known_params]
            if undefined:
                raise ValueError(
                    f"Constraint '{constraint.name}' uses undefined parameters: {undefined}"
                )
        self._constraints_validated = True

    def _extract_constraint_variables(self, rule: str) -> List[str]:
        """
        Extracts all parameter-like variable references from a rule expression.
        Expects qualified names like group.param.
        """
        tokens = re.findall(r"\b([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\b", rule)
        return [f"{group}.{name}" for group, name in tokens]


class DesignConfigWrapper(BaseModel):
    file: Optional[str] = None
    config: Optional[DesignConfig] = None

    @model_validator(mode="before")
    @classmethod
    def load_config(cls, values):
        if "file" in values:
            path = values["file"]
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Design config file not found: {path}")
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            return {
                "file": path,
                "config": DesignConfig(**data)
            }
        else:
            # Assume inline config
            return {
                "file": None,
                "config": DesignConfig(**values)
            }

    def get(self) -> DesignConfig:
        return self.config
