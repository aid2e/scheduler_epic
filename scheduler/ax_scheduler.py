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

    # from botorch.utils.multi_objective.hypervolume import Hypervolume
    # import torch

    AX_AVAILABLE = True
except ImportError:
    AX_AVAILABLE = False

from .trial.trial import Trial
from .trial.trial_state import TrialState
from .job.job import Job, JobType
from .job.multi_steps_job import MultiStepsFunction, MultiStepsJob
from .runners.base_runner import BaseRunner
from .utils.convergence import cal_hv_convergence, cal_single_objective_convergence

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
        self.running_trials = []   # trial_index
        self.trials_metrics = {}   # trial_index -> {"start_time": <>, "end_time": <>, "time_used": <>}
        self.monitoring_interval = self.config.get("monitoring_interval", 10)  # seconds
        self.max_trial_monitoring_time = self.config.get("max_trial_monitoring_time", 86400)  # 24 hours
        self.job_output_dir = self.config.get("job_output_dir", os.path.expanduser("~/ax_scheduler_output"))
        self.cleanup_after_completion = self.config.get("cleanup_after_completion", False)
        self.synchronous = self.config.get("synchronous", False)
        self.max_concurrent_trials = self.config.get("max_concurrent_trials", 1)

        self.early_stopping_threshold = self.config.get("early_stopping_threshold", None)
        self.best_objective_previous = None
        # don't start the early_stopping at the random generation stage
        self.early_stopping_begin_at = self.config.get("early_stopping_begin_at", 0)

        # ref point for hypervolume
        self.ref_point = self.config.get("ref_point", None)

        # checkpoint
        self.restart_from_checkpoint = self.config.get("restart_from_checkpoint", False)
        self.enable_checkpoint = self.config.get("enable_checkpoint", True)
        self.work_dir = self.config.get("work_dir", None)
        self.checkpoint_name = self.config.get("checkpoint_name", None)
        if not self.checkpoint_name:
            self.checkpoint_name = f"{self.experiment.name}.json"
            if self.work_dir:
                if not os.path.exists(self.work_dir):
                    os.makedirs(self.work_dir)
                self.checkpoint_name = os.path.join(self.work_dir, self.checkpoint_name)

        # performance like hv
        self.enable_hv = self.config.get("enable_hv", True)

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

    def add_running_trial(self, trial_index: int):
        """
        Remove a trial_index from the running trials

        Args:
            trial_index: The index of the trial to run
        """
        if trial_index not in self.running_trials:
            self.running_trials.append(trial_index)

    def remove_running_trial(self, trial_index: int):
        """
        Remove a trial_index from the running trials

        Args:
            trial_index: The index of the trial to run
        """
        if trial_index in self.running_trials:
            self.running_trials.remove(trial_index)

    def get_num_of_running_trials(self) -> int:
        """
        Get number of running trials
        """
        return len(self.running_trials)

    def get_num_of_trials(self) -> int:
        """
        Get number of trials
        """
        return len(self.experiment.trials)

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
        self.add_running_trial(trial_index)

        # If synchronous, wait for the trial to complete
        if self.synchronous:
            self.logger.info(f"Waiting trail {trial_index} to finish")
            self._wait_for_trial_completion(trial)
            self.remove_running_trial(trial_index)

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

        self.remove_running_trial(trial_index)

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

    def is_multi_objective(self) -> bool:
        """
        Check whether it's multiple objectives

        Returns:
            Bool value
        """
        if hasattr(self.ax_client.experiment.optimization_config.objective, "objectives") and len(self.ax_client.experiment.optimization_config.objective.objectives) > 1:
            return True
        return False

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

        if self.restart_from_checkpoint:
            self.logger.info("restart from checkpoint: {self.restart_from_checkpoint}")
            self.load_experiment()

        stop_new_trials = False
        converged = 0.0
        continuous_unconverged_trials = 0

        while True:
            num_trials = self.get_num_of_trials()
            num_running = self.get_num_of_running_trials()

            if num_trials >= max_trials and num_running == 0:
                self.logger.info("Reached max trials and all running trials completed.")
                break

            if not stop_new_trials and num_trials < max_trials and num_running < self.max_concurrent_trials:
                if self.early_stopping_threshold is not None and num_trials >= self.early_stopping_begin_at and converged < self.early_stopping_threshold:
                    continuous_unconverged_trials += 1
                else:
                    continuous_unconverged_trials = 0

                if continuous_unconverged_trials > 5:
                    self.logger.info(
                        f"Early stopping: convergence {converged:.6f} "
                        f"below threshold {self.early_stopping_threshold}"
                    )
                    # break  # <-- Important: exit loop on early stopping
                    stop_new_trials = True

                if not stop_new_trials:
                    # Get the next trial
                    trial_index = self.get_next_trial()
                    self.logger.info(f"Got new trial {trial_index}")
                    if trial_index is not None:
                        self.logger.info(f"Running new trial {trial_index}")
                        self.run_trial(trial_index)

            terminated_trials = []
            self.logger.debug(f"Running trials: {self.running_trials}")
            for trial_index in self.running_trials:
                trial = self.trials[trial_index]
                status = trial.check_status()
                self.logger.debug(f"Trial {trial.trial_id} status: {status}")

                if status in [TrialState.COMPLETED, TrialState.FAILED, TrialState.CANCELLED]:
                    if status == TrialState.COMPLETED:
                        self.logger.info(f"Completing trial {trial_index}")
                        self.complete_trial(trial_index)
                        early_stop_decision = self.ax_client.should_stop_trials_early([trial_index])
                        self.logger.debug(f"Trial [{trial_index}] early stop decision: {early_stop_decision}")
                        if early_stop_decision:
                            # self.ax_client.stop_trial_early(trial_index)
                            # break
                            pass
                    terminated_trials.append(trial_index)
                    self.trials_metrics[trial_index] = {
                        "start_time": trial.start_time,
                        "end_time": trial.end_time,
                        "time_used": (trial.end_time - trial.start_time).total_seconds(),
                    }

            has_terminated_trials = False
            if terminated_trials:
                has_terminated_trials = True

            for trial_index in terminated_trials:
                self.remove_running_trial(trial_index)

            if has_terminated_trials and self.enable_checkpoint:
                self.save_experiment()

            # Update convergence after trials complete
            if self.is_multi_objective():
                volume, converged = cal_hv_convergence(self.ax_client, hv_pareto=self.best_objective_previous)
                self.best_objective_previous = volume
                self.logger.info(f"Current hypervolume: {volume:.6f}, convergence: {converged:.6f}")
            else:
                best_obj, converged = cal_single_objective_convergence(self.ax_client, best_objective_previous=self.best_objective_previous, logger=self.logger)
                self.best_objective_previous = best_obj
                self.logger.info(f"Current best objective: {best_obj:.6f}, convergence: {converged:.6f}")

            time.sleep(self.monitoring_interval)

        # Get the best parameters
        if self.is_multi_objective():
            pareto_params = self.ax_client.get_pareto_optimal_parameters()
            return pareto_params
        else:
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

    def save_experiment(self, path: str = None) -> None:
        """
        Save the experiment to a file.

        Args:
            path: Path to save the experiment to
        """
        if path:
            if not path.endswith(".json"):
                path += ".json"
        else:
            path = self.checkpoint_name

        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(path, "w") as f:
            data = {
                "experiment": self.experiment,
                "trials_metrics": self.trials_metrics,
            }
            json_data = object_to_json(data)
            import json

            json.dump(json_data, f, indent=2)
        self.logger.info(f"save experiment to checkpoint file {path}")

    def load_experiment(self, path: str = None) -> None:
        """
        Load an experiment from a file.

        Args:
            path: Path to load the experiment from
        """
        if not path:
            path = self.checkpoint_name

        if os.path.exists(path):
            with open(path, "r") as f:
                import json

                json_data = json.load(f)
                data = object_from_json(json_data)
                self.experiment = data["experiment"]
                self.trials_metrics = data["trials_metrics"]

            # If we had an AxClient, update its experiment
            if self.ax_client is not None:
                self.ax_client._experiment = self.experiment

            self.logger.info(f"load from checkpoint file {path}")
        else:
            self.logger.info(f"checkpoint file {path} doesn't exist")

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
