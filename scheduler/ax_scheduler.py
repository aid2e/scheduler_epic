"""
AxScheduler - Integration with Ax for running trials with our runners.
"""

import logging
import os
import time
import uuid
from typing import Dict, Any, Optional, Callable, Union
from contextlib import contextmanager

# Try importing Ax
try:
    from ax.core.base_trial import BaseTrial
    from ax.core.trial import Trial as AxTrial
    from ax.service.ax_client import AxClient
    from ax.core.experiment import Experiment

    # from ax.core.metric import Metric
    # from ax.core.objective import Objective
    # from ax.core.optimization_config import OptimizationConfig
    from ax.core.arm import Arm
    from ax.storage.json_store.encoder import object_to_json
    from ax.storage.json_store.decoder import object_from_json

    AX_AVAILABLE = True
except ImportError:
    AX_AVAILABLE = False

from .trial.trial import Trial
from .trial.trial_state import TrialState
from .job.job import Job, JobType
from .job.multi_steps_job import MultiStepsFunction, MultiStepsJob
from .runners.base_runner import BaseRunner

# from .utils.common import setup_logging


# setup_logging(log_level='info')


class AxScheduler:
    """
    A scheduler that integrates with Ax for optimization.

    This scheduler allows running Ax trials using different runners.
    """

    def __init__(
        self,
        ax_client_or_experiment: Union[AxClient, Experiment],
        runner: BaseRunner,
        config: Dict[str, Any] = None,
    ):
        """
        Initialize a new AxScheduler.

        Args:
            ax_client_or_experiment: The Ax client or experiment to use for optimization
            runner: The runner to use for executing jobs
            config: Additional configuration options:
                monitoring_interval: Seconds between monitoring checks (default: 10)
                max_trial_monitoring_time: Maximum time to monitor a trial in seconds (default: 86400 = 24 hours)
                job_output_dir: Directory to store job outputs (default: ~/ax_scheduler_output)
                cleanup_after_completion: Whether to clean up job files after completion (default: False)
                synchronous: Whether to run trials synchronously (default: False)
        """
        if not AX_AVAILABLE:
            raise ImportError("Ax is not installed. Install with: pip install ax-platform")

        self.config = config or {}

        # Extract the experiment from the client if a client was provided
        if isinstance(ax_client_or_experiment, AxClient):
            self.ax_client = ax_client_or_experiment
            self.experiment = ax_client_or_experiment.experiment
        else:
            self.ax_client = None
            self.experiment = ax_client_or_experiment

        self.runner = runner
        self.trials = {}  # trial_index -> Trial
        self.monitoring_interval = self.config.get("monitoring_interval", 10)  # seconds
        self.max_trial_monitoring_time = self.config.get("max_trial_monitoring_time", 86400)  # 24 hours
        self.job_output_dir = self.config.get("job_output_dir", os.path.expanduser("~/ax_scheduler_output"))
        self.cleanup_after_completion = self.config.get("cleanup_after_completion", False)
        self.synchronous = self.config.get("synchronous", False)

        # Set up logging
        self.logger = logging.getLogger("AxScheduler")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

        # Create output directory
        os.makedirs(self.job_output_dir, exist_ok=True)

        # Function lookup map for different job types
        self.objective_fn = None
        self.script_path = None
        self.container_image = None
        self.container_command = None
        self.job_type = JobType.FUNCTION

    def set_objective_function(self, objective_fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Set the objective function to optimize.

        Args:
            objective_fn: The objective function to optimize
        """
        self.objective_fn = objective_fn
        if type(self.objective_fn) in [MultiStepsFunction]:
            self.job_type = JobType.MULTISTEPSFUNCTION
        else:
            self.job_type = JobType.FUNCTION

    def set_script_objective(self, script_path: str):
        """
        Set a script to use as the objective function.

        Args:
            script_path: Path to the script to run for each trial
        """
        if not os.path.exists(script_path):
            raise ValueError(f"Script path '{script_path}' does not exist")

        self.script_path = script_path
        self.job_type = JobType.SCRIPT

    def set_container_objective(self, container_image: str, container_command: Optional[str] = None):
        """
        Set a container to use as the objective function.

        Args:
            container_image: Container image to run for each trial
            container_command: Command to run in the container (optional)
        """
        self.container_image = container_image
        self.container_command = container_command
        self.job_type = JobType.CONTAINER

    def _create_trial_from_ax(self, ax_trial: BaseTrial) -> Trial:
        """
        Create a Trial object from an Ax trial.

        Args:
            ax_trial: The Ax trial to convert

        Returns:
            A Trial object
        """
        if not isinstance(ax_trial, AxTrial):
            raise ValueError(f"Expected AxTrial, got {type(ax_trial)}")

        # Create a new trial
        trial_id = f"trial_{ax_trial.index}"
        parameters = ax_trial.arm.parameters if ax_trial.arm else {}
        trial = Trial(trial_id, parameters)

        # Create a job for the trial based on the job type
        job_id = f"{trial_id}_job_{uuid.uuid4().hex[:8]}"

        # Set up working directory for this job
        working_dir = os.path.join(self.job_output_dir, trial_id)
        os.makedirs(working_dir, exist_ok=True)

        # Create job based on job type
        if self.job_type == JobType.FUNCTION:
            if self.objective_fn is None:
                raise ValueError("Objective function not set")

            job = Job(
                job_id=job_id,
                job_type=JobType.FUNCTION,
                function=self.objective_fn,
                params=parameters,
                working_dir=working_dir,
            )

        elif self.job_type == JobType.SCRIPT:
            if self.script_path is None:
                raise ValueError("Script path not set")

            job = Job(
                job_id=job_id,
                job_type=JobType.SCRIPT,
                script_path=self.script_path,
                params=parameters,
                working_dir=working_dir,
                output_files=["result.json"],
            )

        elif self.job_type == JobType.CONTAINER:
            if self.container_image is None:
                raise ValueError("Container image not set")

            job = Job(
                job_id=job_id,
                job_type=JobType.CONTAINER,
                container_image=self.container_image,
                container_command=self.container_command,
                params=parameters,
                working_dir=working_dir,
                output_files=["result.json"],
            )

        elif self.job_type == JobType.MULTISTEPSFUNCTION:
            if self.objective_fn is None:
                raise ValueError("Objective function not set")

            job = MultiStepsJob(
                job_id=job_id,
                job_type=JobType.MULTISTEPSFUNCTION,
                function=self.objective_fn,
                params=parameters,
                working_dir=working_dir,
                trial_id=trial_id,
            )

        else:
            raise ValueError(f"Unsupported job type: {self.job_type}")

        # Set the runner for the job
        job.set_runner(self.runner)

        # Add the job to the trial
        trial.add_job(job)

        return trial

    def run_trial(self, trial_index: int) -> Trial:
        """
        Run a specific trial.

        Args:
            trial_index: The index of the trial to run

        Returns:
            The Trial object
        """
        self.logger.debug(f"start to run trial: {trial_index}")
        # Get the Ax trial
        ax_trial = self.experiment.trials[trial_index]

        # Create a Trial object
        trial = self._create_trial_from_ax(ax_trial)
        self.trials[trial_index] = trial
        self.logger.debug(f"Created trial {trial_index} from ax trail: {trial}")

        # Run the trial
        self.logger.info(f"Running trial {trial_index} with parameters: {ax_trial.arm.parameters}")
        trial.run()

        # If synchronous, wait for the trial to complete
        if self.synchronous:
            self.logger.info(f"Waiting trail {trial_index} to finish")
            self._wait_for_trial_completion(trial)

        return trial

    def _wait_for_trial_completion(self, trial: Trial) -> None:
        """
        Wait for a trial to complete.

        Args:
            trial: The trial to wait for
        """
        start_time = time.time()
        while True:
            status = trial.check_status()
            self.logger.debug(f"Trail {trial.trial_id} status: {status}")

            if status in [
                TrialState.COMPLETED,
                TrialState.FAILED,
                TrialState.CANCELLED,
            ]:
                break

            # Check if we've been monitoring for too long
            if time.time() - start_time > self.max_trial_monitoring_time:
                self.logger.warning(f"Trial {trial.trial_id} monitoring timed out after {self.max_trial_monitoring_time} seconds")
                break

            time.sleep(self.monitoring_interval)

    def get_next_trial(self) -> Optional[int]:
        """
        Generate a new trial using Ax and return its index.

        Returns:
            The index of the new trial, or None if no more trials can be generated
        """
        if self.ax_client is None:
            raise ValueError("An AxClient is required to generate new trials")

        try:
            _, trial_index = self.ax_client.get_next_trial()
            return trial_index
        except Exception as e:
            self.logger.error(f"Error generating next trial: {str(e)}")
            return None

    def complete_trial(self, trial_index: int, raw_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark a trial as completed in Ax.

        Args:
            trial_index: The index of the trial to complete
            raw_data: Raw data to attach to the trial
        """
        self.logger.info(f"Completing trial {trial_index}")

        trial = self.trials.get(trial_index)
        if trial is None:
            raise ValueError(f"Trial {trial_index} not found")

        # Get the results
        if raw_data is None:
            raw_data = trial.get_results()
        self.logger.debug(f"Trial {trial_index} results(raw data): {raw_data}")

        # Complete the trial in Ax
        if self.ax_client is not None:
            self.ax_client.complete_trial(trial_index=trial_index, raw_data=raw_data)
        else:
            # If we don't have an AxClient, update the trial directly in the experiment
            ax_trial = self.experiment.trials[trial_index]
            for metric_name, value in raw_data.items():
                if isinstance(value, dict) and "value" in value:
                    ax_trial.run().add_metric_outcome(
                        metric_name=metric_name,
                        mean=value["value"],
                        sem=value.get("sem", 0.0),
                    )
                else:
                    ax_trial.run().add_metric_outcome(metric_name=metric_name, mean=value)

        # Clean up if configured to do so
        if self.cleanup_after_completion:
            self._cleanup_trial(trial)

    def _cleanup_trial(self, trial: Trial) -> None:
        """
        Clean up files for a completed trial.

        Args:
            trial: The trial to clean up
        """
        self.logger.info(f"Clean trial {trial.trial_id}")
        for job in trial.jobs:
            if hasattr(job, "working_dir") and os.path.exists(job.working_dir):
                import shutil

                try:
                    shutil.rmtree(job.working_dir)
                except Exception as e:
                    self.logger.warning(f"Error cleaning up trial directory: {str(e)}")

    def run_optimization(self, max_trials: int = 10) -> Dict[str, Any]:
        """
        Run the optimization process.

        Args:
            max_trials: Maximum number of trials to run

        Returns:
            The best parameters found
        """
        self.logger.info("run optimization")
        if self.ax_client is None:
            raise ValueError("An AxClient is required to run optimization")

        for _ in range(max_trials):
            # Get the next trial
            trial_index = self.get_next_trial()
            self.logger.info(f"Got new trial {trial_index}")
            if trial_index is None:
                break

            # Run the trial
            self.logger.info(f"Running new trial {trial_index}")
            trial = self.run_trial(trial_index)

            # If not synchronous, we need to monitor the trial
            if not self.synchronous:
                self.logger.info(f"Waiting trial {trial_index} to finish")
                # Monitor the trial until it's done
                while trial.check_status() not in [
                    TrialState.COMPLETED,
                    TrialState.FAILED,
                    TrialState.CANCELLED,
                ]:
                    time.sleep(self.monitoring_interval)
                self.logger.debug(f"trial {trial_index} status: {trial.check_status()}")

            # Complete the trial
            self.logger.info(f"checking to complete trial {trial_index}")
            if trial.state == TrialState.COMPLETED:
                self.logger.info(f"Completing trial {trial_index}")
                self.complete_trial(trial_index)

        # Get the best parameters
        best_parameters, _ = self.ax_client.get_best_parameters()
        return best_parameters

    def monitor_trials(self) -> None:
        """
        Monitor all running trials.
        """
        self.logger.debug("Monitoring trials")
        for trial_index, trial in self.trials.items():
            trial_state = trial.check_status()

            if trial_state == TrialState.COMPLETED and trial_index in self.experiment.trials:  # noqa W503
                ax_trial = self.experiment.trials[trial_index]
                if not ax_trial.status.is_completed:
                    self.complete_trial(trial_index)
        self.logger.debug("Finished to monitor trials")

    def save_experiment(self, path: str) -> None:
        """
        Save the experiment to a file.

        Args:
            path: Path to save the experiment to
        """
        if not path.endswith(".json"):
            path += ".json"

        with open(path, "w") as f:
            json_data = object_to_json(self.experiment)
            import json

            json.dump(json_data, f, indent=2)

    def load_experiment(self, path: str) -> None:
        """
        Load an experiment from a file.

        Args:
            path: Path to load the experiment from
        """
        with open(path, "r") as f:
            import json

            json_data = json.load(f)
            self.experiment = object_from_json(json_data)

        # If we had an AxClient, update its experiment
        if self.ax_client is not None:
            self.ax_client._experiment = self.experiment

    @contextmanager
    def batch_trial_context(self):
        """
        Context manager for creating and running a batch of trials.

        This is useful for running multiple trials in parallel.

        Example:
            ```python
            with scheduler.batch_trial_context() as batch:
                for i in range(5):
                    params = {'x': i * 0.1, 'y': i * 0.2}
                    batch.add_trial(params)

                batch.run()
            ```
        """
        batch = _TrialBatch(self)
        try:
            yield batch
        finally:
            batch.run()


class _TrialBatch:
    """Helper class for creating and running a batch of trials."""

    def __init__(self, scheduler: AxScheduler):
        self.scheduler = scheduler
        self.trials_to_run = []
        self.parameters_list = []

    def add_trial(self, parameters: Dict[str, Any]) -> None:
        """
        Add a trial to the batch.

        Args:
            parameters: Parameters for the trial
        """
        self.parameters_list.append(parameters)

    def run(self) -> None:
        """Run all trials in the batch."""
        if self.scheduler.ax_client is None:
            raise ValueError("An AxClient is required to run a batch of trials")

        # Create trials in Ax
        trial_indices = []
        for parameters in self.parameters_list:
            arm = Arm(parameters=parameters)
            trial_index = self.scheduler.ax_client.attach_trial(arm)[0]
            trial_indices.append(trial_index)

        # Run trials
        for trial_index in trial_indices:
            self.scheduler.run_trial(trial_index)

        # If synchronous, trials are already completed
        # Otherwise, we need to monitor them
        if not self.scheduler.synchronous:
            # Monitor trials until they're all done
            all_done = False
            while not all_done:
                all_done = True
                for trial_index in trial_indices:
                    trial = self.scheduler.trials.get(trial_index)
                    if trial and trial.check_status() not in [
                        TrialState.COMPLETED,
                        TrialState.FAILED,
                        TrialState.CANCELLED,
                    ]:
                        all_done = False
                        break

                if not all_done:
                    time.sleep(self.scheduler.monitoring_interval)

        # Complete trials
        for trial_index in trial_indices:
            trial = self.scheduler.trials.get(trial_index)
            if trial and trial.state == TrialState.COMPLETED:
                self.scheduler.complete_trial(trial_index)
