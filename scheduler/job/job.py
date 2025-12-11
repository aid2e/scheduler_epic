"""
Job - Defines a job that can be run by a runner.
"""

import copy
import logging
from typing import Dict, Any, Optional, Callable, List
from enum import Enum, auto
import os
from datetime import datetime

class JobState(Enum):
    """
    Enum representing the possible states of a job.
    """

    NEW = auto()
    CREATED = auto()
    READY = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    PAUSED = auto()
    CANCELLED = auto()
    RUNNINGNOMONITOR = auto()
    
    def __str__(self):
        return self.name

class JobType(Enum):
    """Type of job to run."""

    FUNCTION = "function"  # Python function
    SCRIPT = "script"  # Shell script or Python script
    CONTAINER = "container"  # Docker/Singularity container
    MULTISTEPSFUNCTION = "multistepsfunction"  # Multiple python function

class BaseJob:
    """
    Base class for jobs.
    """
    def __init__(self, job_id: str
                 ):
        """
        Initialize a new BaseJob.

        Args:
            job_id: Unique identifier for the job.
        """
        self.job_id = job_id

class Job:
    """
    A job that can be run by a runner.

    Each job has a state that is tracked. Jobs can be one of several types:
    - Function: A Python function to run
    - Script: A shell or Python script to execute
    - Container: A container to run
    """

    def __init__(
        self,
        job_id: str,
        job_type: JobType = JobType.FUNCTION,
        function: Optional[Callable] = None,
        script_path: Optional[str] = None,
        container_image: Optional[str] = None,
        container_command: Optional[str] = None,
        params: Dict[str, Any] = None,
        env_vars: Dict[str, str] = None,
        init_env: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        output_files: Optional[List[str]] = None,
        parent_result_parameter_name: Optional[str] = "parent_result_parameter",
        return_func_results: bool = True,
        with_output_dataset: bool = False,
        output_file: str = None,
        output_dataset: str = None,
        num_events: int = 1,
        num_events_per_job: int = 1,
        with_input_datasets: bool = False,
        input_datasets: dict = {},
        **kwargs,
    ):
        """
        Initialize a new job.

        Args:
            job_id: Unique identifier for the job
            job_type: Type of job (FUNCTION, SCRIPT, or CONTAINER)
            function: The function to run for this job (if job_type is FUNCTION)
            script_path: Path to the script to run (if job_type is SCRIPT)
            container_image: Container image to run (if job_type is CONTAINER)
            container_command: Command to run in the container (if job_type is CONTAINER)
            params: Parameters to pass to the function or script
            env_vars: Environment variables to set for the job
            working_dir: Working directory for the job
            output_files: List of output files to collect after job completion
        """
        self.job_id = job_id
        self.job_type = job_type
        self.function = function
        self.script_path = script_path
        self.container_image = container_image
        self.container_command = container_command
        self.params = params or {}
        self.env_vars = env_vars or {}
        self.init_env = init_env or []
        self.working_dir = working_dir
        self.output_files = output_files or []

        self.state = JobState.CREATED
        self.creation_time = datetime.now()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}
        self.runner = None
        self.extra_args = kwargs
        # Validate job configuration
        self._validate()

        self.parent_results = None
        self.parent_result_parameter_name = parent_result_parameter_name

        self.return_func_results = return_func_results

        self.with_output_dataset = with_output_dataset
        self.output_file = output_file
        self.output_dataset = output_dataset
        self.num_events = num_events
        self.num_events_per_job = num_events_per_job
        self.with_input_datasets = with_input_datasets
        self.input_datasets = input_datasets

        self.internal_id = None
        self.parent_internal_id = None
        self.logs = {"stdout": None, "stderr": None} #path to stdout and stderr logs
        self.logger = logging.getLogger("Job")

    def _validate(self):
        """Validate that the job is properly configured."""
        if self.job_type == JobType.FUNCTION and self.function is None:
            raise ValueError("Function must be provided for FUNCTION job type")

        if self.job_type == JobType.SCRIPT and (self.script_path is None or not os.path.exists(self.script_path)):
            raise ValueError(f"Script path '{self.script_path}' must be provided and exist for SCRIPT job type")

        if self.job_type == JobType.CONTAINER and self.container_image is None:
            raise ValueError("Container image must be provided for CONTAINER job type")

    def set_internal_id(self, internal_id) -> None:
        """
        Set internal id for the job.

        Args:
            internal_id: The internal id for the job.
        """
        self.internal_id = internal_id

    def set_parent_results(self, step, objective, job_key, results) -> None:
        """
        Set results for the parent job.

        Args:
            step: The step name of the curret job
            objective: The objective of the current job
            job_key: The job key of the curret job
            results: Results from the parent job
        """
        self.logger.info(f"Set parent results for job {self.job_id} step {step} job_key {job_key}: {results}")
        self.parent_results = results
        if self.parent_result_parameter_name and results:
            old_params = copy.deepcopy(self.params)
            self.params[self.parent_result_parameter_name] = results.get(self.parent_result_parameter_name, None)
            self.logger.info(f"Change parameters for job {self.job_id} step {step} job_key {job_key} from {old_params} to {self.params}")

    def set_runner(self, runner) -> None:
        """
        Set the runner for this job.

        Args:
            runner: The runner to use for this job
        """
        self.runner = runner

    def run(self) -> None:
        """
        Run this job using its assigned runner.

        Raises:
            ValueError: If no runner has been assigned
        """
        self.logger.info(f"Run job {self.job_id} with runner: {self.runner}")
        if not self.runner:
            raise ValueError("No runner assigned to this job")

        self.state = JobState.RUNNING
        self.start_time = datetime.now()
        self.runner.run_job(self)

    def check_status(self) -> None:
        """
        Run to check the status of the job.
        """
        if self.state not in [JobState.NEW, JobState.READY, JobState.CREATED, JobState.COMPLETED, JobState.FAILED]:
            if self.return_func_results:
                self.runner.check_job_status(self)

    def is_running(self) -> bool:
        """
        Check if the job is running.

        Returns:
            True if the job is running, False otherwise
        """
        return self.state == JobState.RUNNING

    def is_completed(self) -> bool:
        """
        Check if the job is completed.

        Returns:
            True if the job is completed, False otherwise
        """
        return self.state == JobState.COMPLETED

    def has_failed(self) -> bool:
        """
        Check if the job has failed.

        Returns:
            True if the job has failed, False otherwise
        """
        return self.state == JobState.FAILED

    def complete(self, results: Dict[str, Any]) -> None:
        """
        Mark the job as completed and store its results.

        Args:
            results: The results of the job
        """
        self.logger.info(f"Complete job {self.job_id}")
        self.state = JobState.COMPLETED
        self.end_time = datetime.now()
        self.results = results

    def fail(self, error: Optional[str] = None) -> None:
        """
        Mark the job as failed and store the error.

        Args:
            error: The error that caused the job to fail
        """
        self.logger.error(f"Fail job {self.job_id}, error: {error}")
        self.state = JobState.FAILED
        self.end_time = datetime.now()
        if error:
            self.results["error"] = error
        raise Exception(f"Job {self.job_id} failed: {error}")

    def get_results(self) -> Dict[str, Any]:
        """
        Get the results of this job.

        Returns:
            Dictionary of results
        """
        return self.results

    def set_metrics(self, metrics: Optional[Dict[str, Any]] = None) -> None:
        """
        Set job's metrics

        Args:
            metrics: Dictionary of job metrics
        """
        self.metrics = metrics

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics of this job.

        Returns:
            Dictionary of metrics
        """
        return self.metrics

    def cancel(self) -> None:
        """
        Cancel the job.
        """
        self.runner.cancel_job(self)

class ParallelJob(Job):
    """
    A Job subclass that can manage parallel subjobs.

    Each subjob is itself a Job instance (usually SCRIPT or FUNCTION type),
    managed under the same runner context.
    """

    def __init__(
        self,
        job_id: str,
        subjobs: Optional[List[Job]] = None,
        sequential_steps: Optional[List["ParallelJob"]] = None,
        *args,
        **kwargs,
    ):
        """
        Initialize a new ParallelJob.

        Args:
            job_id: Unique identifier for the parallel job.
            subjobs: Optional list of Job objects to run in parallel.
            sequential_steps: Optional list of ParallelJob objects for sequential execution.
            *args: Variable length argument list passed to parent Job class.
            **kwargs: Arbitrary keyword arguments passed to parent Job class.
        """
        super().__init__(job_id, *args, **kwargs)
        self.subjobs = subjobs or []  # Parallel subjobs
        self.sequential_steps = sequential_steps or []  # For Multi-step jobs
        self.logger = logging.getLogger(f"ParallelJob[{job_id}]")
        self.logger.setLevel(logging.DEBUG)

    # -------------------------------
    # Subjob handling
    # -------------------------------
    def add_subjob(self, subjob: Job):
        """
        Add a subjob to be run in parallel.

        Args:
            subjob: The Job object to add to the parallel execution list.
        """
        self.subjobs.append(subjob)

    def run_subjobs(self):
        """Run all subjobs in parallel (runner decides how)."""
        if not self.subjobs:
            return

        self.logger.info(f"Running {len(self.subjobs)} subjobs for {self.job_id}")

        for subjob in self.subjobs:
            subjob.set_runner(self.runner)
            subjob.run()

        # Optionally, poll until all complete
        while not all(sj.is_completed() or sj.has_failed() for sj in self.subjobs):
            for sj in self.subjobs:
                sj.check_status()

        # Aggregate subjob results
        self._aggregate_subjob_results()

    def _aggregate_subjob_results(self):
        """Combine all subjob results into a single result dictionary."""
        all_results = [sj.get_results() for sj in self.subjobs if sj.is_completed()]
        if not all_results:
            self.fail("No successful subjob results found")
            return

        # Default aggregation: mean objective if numeric
        merged = {}
        for result in all_results:
            for k, v in result.items():
                if isinstance(v, (int, float)):
                    merged.setdefault(k, []).append(v)
                else:
                    merged.setdefault(k, []).append(v)

        aggregated = {k: sum(v) / len(v) if isinstance(v[0], (int, float)) else v for k, v in merged.items()}
        self.complete(aggregated)

    # -------------------------------
    # Multi-step handling
    # -------------------------------
    def run(self):
        """Override base run to support multi-step parallel execution."""
        self.logger.info(f"Running ParallelJob {self.job_id}")
        self.state = JobState.RUNNING
        self.start_time = datetime.now()

        if not self.sequential_steps:
            # No steps — just run subjobs directly
            self.run_subjobs()
            return

        # Execute each step sequentially
        for step in self.sequential_steps:
            self.logger.info(f"Starting step {step.job_id} for {self.job_id}")
            step.set_runner(self.runner)
            step.run()
            if step.has_failed():
                self.fail(f"Step {step.job_id} failed")
                return
            self.logger.info(f"Completed step {step.job_id}")

        self.state = JobState.COMPLETED
        self.end_time = datetime.now()
        self.logger.info(f"ParallelJob {self.job_id} completed successfully")
