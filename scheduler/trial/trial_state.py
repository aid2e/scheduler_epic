"""
TrialState - Defines the possible states of a trial.
"""

from enum import Enum, auto


class TrialState(Enum):
    """
    Enum representing the possible states of a trial.
    """
    CREATED = auto()
    QUEUED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    PAUSED = auto()
    CANCELLED = auto()
    
    def __str__(self):
        return self.name