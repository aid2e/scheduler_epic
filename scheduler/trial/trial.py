"""
Trial - Extension of Ax trial with additional functionality.
"""

import logging

from typing import Dict, List, Optional, Any
from datetime import datetime
from .trial_state import TrialState
from ..job.job import Job


class Trial:
    """
    A trial class that extends Ax trial functionality.

    A trial can contain multiple jobs and has a state that is tracked.
    """

    def __init__(self, trial_id: str, parameters: Dict[str, Any]):
        """
        Initialize a new trial.

        Args:
            trial_id: Unique identifier for the trial
            parameters: Dictionary of parameters for this trial
        """
        self.trial_id = trial_id
        self.parameters = parameters
        self.jobs: List[Job] = []
        self.state = TrialState.CREATED
        self.creation_time = datetime.now()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}

        self.logger = logging.getLogger("Trial")
        self.num_checks = 0

    def add_job(self, job: Job) -> None:
        """
        Add a job to this trial.

        Args:
            job: The job to add
        """
        self.jobs.append(job)

    def run(self) -> None:
        """
        Run all jobs in this trial.
        """
        self.logger.info(f"Running trial {self.trial_id}")
        self.state = TrialState.RUNNING
        self.start_time = datetime.now()

        for job in self.jobs:
            job.run()

    def check_status(self) -> TrialState:
        """
        Check the status of all jobs and update the trial state.

        Returns:
            The current state of the trial
        """
        for job in self.jobs:
            job.check_status()

        # If any job is still running, the trial is running
        if any(job.is_running() for job in self.jobs):
            self.state = TrialState.RUNNING
        # If all jobs are completed, the trial is completed
        elif all(job.is_completed() for job in self.jobs):
            self.state = TrialState.COMPLETED
            if not self.end_time:
                self.end_time = datetime.now()
        # If any job has failed, the trial has failed
        elif any(job.has_failed() for job in self.jobs):
            self.state = TrialState.FAILED
            if not self.end_time:
                self.end_time = datetime.now()

        if self.num_checks % 60 == 0:
            self.logger.info(f"Checking trial {self.trial_id} status: {self.state}")
        self.num_checks += 1

        return self.state

    def get_results(self) -> Dict[str, Any]:
        """
        Gather results from all jobs.

        Returns:
            Dictionary of results
        """
        for job in self.jobs:
            if job.is_completed():
                # Merge job results with trial results
                self.results.update(job.get_results())

        return self.results
