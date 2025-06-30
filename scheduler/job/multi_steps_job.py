"""
Job - Defines a job that can be run by a runner.
"""

import copy
import logging
from datetime import datetime
from itertools import product
from typing import Dict, Any, Optional, List
from .job import Job, JobType
from .job_state import JobState


class MultiStepsFunction(object):
    """
    A class to manage multiple function and runners.
    """

    def __init__(
        self,
        objective_funcs,
        deps=None,
        final=None,
        global_parameters=None,
        global_parameters_steps=[],
    ):
        self.objective_funcs = objective_funcs
        self.deps = deps

        # if final is not set, it will use the last step in objective_funcs.
        # The final step will set its result as the job's result
        self.final = final

        # it's used to generate additional parameters.
        # for example with this global parameters below:
        #     g = {"param1": ["a", "b"], "param2": [1, 2]}
        # it will generate a list of parameters:
        # [{"param1": "a", "param2": 1}, {"param1": "a", "param2": 2},
        #  {"param1": "b", "param2": 1}, {"param1": "b", "param2": 1}]
        # Every item in the list will be added to the hyperparameters to generate new jobs
        # For example, with {"param1": "a", "param2": 1}, it will generate
        # a new job with function(**hyperparameter, param1="a", param2=b)
        # So if global parameter is used, you need to leave parameter sigatures for global
        # parameters in your function.
        # in the final function, you need to wat to merge the results to different objectives
        self.global_parameters = global_parameters
        self.global_parameters_steps = global_parameters_steps


class MultiStepsJob(Job):
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
        job_type: JobType = JobType.MULTISTEPSFUNCTION,
        function: Optional[MultiStepsFunction] = None,
        params: Dict[str, Any] = None,
        env_vars: Dict[str, str] = None,
        working_dir: Optional[str] = None,
        output_files: Optional[List[str]] = None,
        parent_result_parameter_name="parent_result_parameter",
    ):
        """
        Initialize a new job.

        Args:
            job_id: Unique identifier for the job
            job_type: Type of job (MULFUNCTION)
            function: The function to run for this job
            params: Parameters to pass to the function or script
            env_vars: Environment variables to set for the job
            working_dir: Working directory for the job
            output_files: List of output files to collect after job completion
        """
        self.job_id = job_id
        self.job_type = job_type
        self.function = function
        self.params = params or {}
        self.env_vars = env_vars or {}
        self.working_dir = working_dir
        self.output_files = output_files or []

        self.state = JobState.CREATED
        self.creation_time = datetime.now()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}
        self.runner = None

        # Validate job configuration
        self._validate()
        self._initialize()

        self.step_jobs = {}
        self.deps = {}

        # if final is not set, it will use the last step in objective_funcs.
        # The final step will set its result as the job's result
        self.final = None

        self.global_parameters = []
        self.global_parameters_steps = []

        self.parent_results = None
        self.parent_result_parameter_name = parent_result_parameter_name

        self.logger = logging.getLogger("Job")

    def _validate(self):
        """Validate that the job is properly configured."""
        if not self.job_type == JobType.MULTISTEPSFUNCTION:
            raise ValueError("Job type must be MULFUNCTION")
            if self.function is None:
                raise ValueError("Function must be provided for MULTISTEPSFUNCTION job type")
            elif not isinstance(self.function, MultiStepsFunction):
                raise ValueError("MultiStepsFunction must be provided for MULTISTEPSFUNCTION job type")

    def get_step_job(
        self,
        job_type,
        runner,
        func=None,
        script_path=None,
        container_image=None,
        container_command=None,
    ) -> Job:
        if job_type == JobType.FUNCTION:
            job = Job(
                job_id=self.job_id,
                job_type=job_type,
                function=func,
                params=self.params,
                working_dir=self.working_dir,
            )
        elif self.job_type == JobType.SCRIPT:
            job = Job(
                job_id=self.job_id,
                job_type=job_type,
                script_path=script_path,
                params=self.params,
                working_dir=self.working_dir,
                output_files=["result.json"],
            )
        elif self.job_type == JobType.CONTAINER:
            job = Job(
                job_id=self.job_id,
                job_type=job_type,
                container_image=container_image,
                container_command=container_command,
                params=self.params,
                working_dir=self.working_dir,
                output_files=["result.json"],
            )
        else:
            raise ValueError(f"Unsupported job type: {self.job_type}")

        job.set_runner(runner)

    def get_key_from_dict(key):
        if not key:
            return "None"
        return tuple(sorted(key.items()))

    def _initialize(self):
        objective_funcs = self.function.objective_funcs
        deps = self.function.deps
        if self.function.global_parameters:
            self.global_parameters = [dict(zip(self.global_parameters.keys(), values)) for values in product(*self.global_parameters.values())]
        self.global_parameters_steps = self.function.global_parameters_steps

        for step_name in objective_funcs:
            func = objective_funcs[step_name].get("func", None)
            script_path = objective_funcs[step_name].get("script_path", None)
            container_image = objective_funcs[step_name].get("container_image", None)
            container_command = objective_funcs[step_name].get("container_command", None)
            job_type = objective_funcs[step_name].get("job_type", JobType.FUNCTION)
            runner = objective_funcs[step_name]["runner"]
            if not runner:
                runner = self.runner

            if not self.global_parameters or step_name not in self.global_parameters_steps:
                step_job = self.get_step_job(
                    job_type,
                    runner,
                    func=func,
                    additional_parameters=None,
                    script_path=script_path,
                    container_image=container_image,
                    container_command=container_command,
                )
                g_params = self.get_key_from_dict(None)
                self.step_jobs[step_name] = {g_params: step_job}
            else:
                self.step_jobs[step_name] = {}
                for g_params in self.global_parameters:
                    step_job = self.get_step_job(
                        job_type,
                        runner,
                        func=func,
                        additional_parameters=g_params,
                        script_path=script_path,
                        container_image=container_image,
                        container_command=container_command,
                    )
                    g_params_key = self.get_key_from_dict(g_params)
                    self.step_jobs[step_name][g_params_key] = step_job
        self.deps = {}
        if deps:
            for dep in deps:
                if type(deps[dep]) in [str]:
                    self.deps[dep] = {"parent": deps[dep], "state": JobState.NEW, "dep_type": "results"}
                elif type(deps[dep]) in [dict]:
                    self.deps[dep] = {"parent": deps[dep]["parent"], "state": JobState.NEW, "dep_type": deps[dep].get("dep_type", "results")}

        if not self.final:
            for step_name in self.step_jobs:
                # last step_name
                self.final = step_name

    def get_ready_steps(self):
        if self.state in [JobState.COMPLETED, JobState.FAILED]:
            return {}

        readys = []
        for step_name in self.step_jobs:
            if (step_name not in self.deps or self.deps[step_name].get("state", JobState.NEW) == JobState.READY) and self.step_jobs[step_name].state not in [JobState.COMPLETED, JobState.FAILED, JobState.RUNNING, JobState.PAUSED, JobState.CANCELLED]:
                readys.append(step_name)
        return readys

    def set_runner(self, runner) -> None:
        """
        Set the runner for this job.

        Args:
            runner: The runner to use for this job
        """
        self.runner = runner

    def set_parent_results(self, results) -> None:
        self.logger.inf(f"Set parent results for job {self.job_id}: {results}")
        self.parent_results = results
        if self.parent_result_parameter_name and results:
            old_params = copy.deepcopy(self.params)
            self.params[self.parent_result_parameter_name] = results
            self.logger.info(f"Change parameters for job {self.job_id} from {old_params} to {self.params}")

    def get_parent_results(self, step_name, g_param_key) -> object:
        if step_name not in self.deps:
            return None
        parent = self.deps[step_name].get("parent", None)
        dep_type = self.deps[step_name].get("dep_type", "results")
        dep_map = self.deps[step_name].get("dep_map", "one2one")
        parent_jobs = self.step_jobs.get(parent, {})
        if dep_type in ["datasets"]:
            # depend on the rucio dataset name
            return None
        if not parent_jobs:
            # not parent jobs
            return None
        if dep_map == "one2one":
            parent_job = parent_jobs.get(g_param_key, None)
            results = parent_job.results
            return results
        elif dep_map == "all2one":
            results = {}
            for k in parent_jobs:
                parent_job = parent_jobs[k]
                results[k] = parent_job.results
            return results
        return None

    def run_ready_steps(self) -> None:
        """
        Run ready steps
        """
        ready_steps = self.get_ready_steps()
        for step in ready_steps:
            for g_param_key in self.step_jobs[step]:
                step_job = self.step_jobs[step][g_param_key]
                parent_results = self.get_parent_results(step, g_param_key)
                step_job.set_parent_results(parent_results)
                step_job.run()

    def run(self) -> None:
        """
        Run this job using its assigned runner.
        """
        self.state = JobState.RUNNING
        self.start_time = datetime.now()
        self.run_ready_steps()

    def check_status(self) -> None:
        if self.state in [JobState.COMPLETED, JobState.FAILED]:
            return

        # check the steps
        for step_name in self.step_jobs:
            for g_param_key in self.step_jobs[step_name]:
                self.step_jobs[step_name][g_param_key].check_status()

        # if the final step terminates, terminate the job
        if self.step_jobs[self.final].is_completed() or self.step_jobs[self.final].has_failed():
            self.complete(self.results)
            return
        elif self.step_jobs[self.final].has_failed():
            self.fail(self.results)
            return

        # check the dependencies
        for dep in self.deps:
            if self.deps[dep]["state"] not in [JobState.READY]:
                parent = self.deps[dep]["parent"]
                if self.step_jobs[parent].is_completed() or self.step_jobs[parent].has_failed():
                    self.deps[dep]["state"] = JobState.READY

        # run ready steps
        self.run_ready_steps()

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
        self.state = JobState.COMPLETED
        self.end_time = datetime.now()
        self.results = results

    def fail(self, error: Optional[str] = None) -> None:
        """
        Mark the job as failed and store the error.

        Args:
            error: The error that caused the job to fail
        """
        self.state = JobState.FAILED
        self.end_time = datetime.now()
        if error:
            self.results["error"] = error

    def get_results(self) -> Dict[str, Any]:
        """
        Get the results of this job.

        Returns:
            Dictionary of results
        """
        return self.results
