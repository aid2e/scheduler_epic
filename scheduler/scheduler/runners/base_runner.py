"""
BaseRunner - Abstract base class for job runners.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseRunner(ABC):
    """
    Abstract base class for job runners.
    
    Runners are responsible for executing jobs on different
    systems (local, Slurm, PanDA, etc.).
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize a new runner.
        
        Args:
            config: Configuration for the runner
        """
        self.config = config or {}
    
    @abstractmethod
    def run_job(self, job) -> None:
        """
        Run a job.
        
        Args:
            job: The job to run
        """
        pass
    
    @abstractmethod
    def check_job_status(self, job) -> None:
        """
        Check the status of a job and update its state.
        
        Args:
            job: The job to check
        """
        pass
    
    @abstractmethod
    def cancel_job(self, job) -> None:
        """
        Cancel a job.
        
        Args:
            job: The job to cancel
        """
        pass