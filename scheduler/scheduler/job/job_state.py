"""
JobState - Defines the possible states of a job.
"""

from enum import Enum, auto


class JobState(Enum):
    """
    Enum representing the possible states of a job.
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