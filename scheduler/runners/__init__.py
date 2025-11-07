# Copyright (C) 2025 AID2E
# author Karthik Suresh <ksuresh@wm.edu>
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Type

from .base_runner import BaseRunner
from .joblib_runner import JobLibRunner
from .pandaidds_runner import PanDAiDDSRunner
from .slurm_runner import SlurmRunner

__all__ = [
    "BaseRunner",
    "JobLibRunner",
    "PanDAiDDSRunner",
    "SlurmRunner",
    "get_runner",
]


RUNNERS: Dict[str, Type[BaseRunner]] = {
    "joblib": JobLibRunner,
    "panda-idds": PanDAiDDSRunner,
    "slurm": SlurmRunner,
}


def get_runner(name: str, **kwargs: Any) -> BaseRunner:
    """
    Get a runner by name.
    """
    return RUNNERS[name](**kwargs)

def available_runners() -> Dict[str, Type[BaseRunner]]:
    """
    Get the available runners.
    """
    return RUNNERS