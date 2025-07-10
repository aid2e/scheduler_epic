"""
Job - Defines a job that can be run by a runner.
"""

import copy
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from itertools import product
from typing import Dict, Any, Optional, List, Union
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
        """
        Initialize MultiStepsFunction.

        Args:
            objective_funcs: Objective functions as a dict.
            deps: The dependency map between different objective functions.
            final: The last objective functions.
            global_parameters: Global parameters.
            global_parameters_steps: Steps that need to apply global parameters.
        """
        self.objective_funcs = objective_funcs
        self.__name__ = f"mul_func.{'_'.join([k for k in self.objective_funcs])}"
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
    A job that supports multiple steps (multiple sub-jobs).

    Each step is a job with different runners.
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
        trial_id=None,
        return_func_results: bool = True,
        with_output_dataset: bool = False,
        output_file: str = None,
        output_dataset: str = None,
        num_events: int = 1,
        num_events_per_job: int = 1,
        with_input_datasets: bool = False,
        input_datasets: dict = {},
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
        self.trial_id = trial_id
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

        self.step_jobs = {}
        self.step_states = {}
        self.deps = {}

        # if final is not set, it will use the last step in objective_funcs.
        # The final step will set its result as the job's result
        self.final = None

        self.global_parameters = []
        self.global_parameters_steps = []

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

        self.logger = logging.getLogger("MultiStepsJob")

        self._initialize()

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
        additional_parameters=None,
        parent_result_parameter_name=None,
        return_func_results=True,
        with_output_dataset=False,
        output_file=None,
        output_dataset=None,
        num_events=1,
        num_events_per_job=1,
        with_input_datasets=False,
        input_datasets={},
    ) -> Job:
        """
        Generate a job from a step configuration.
        """
        new_params = copy.deepcopy(self.params)
        if additional_parameters:
            new_params.update(additional_parameters)

        # Create a job for the trial based on the job type
        job_id = f"{self.trial_id}_job_{uuid.uuid4().hex[:8]}"

        if job_type == JobType.FUNCTION:
            job = Job(
                job_id=job_id,
                job_type=job_type,
                function=func,
                params=new_params,
                working_dir=self.working_dir,
                parent_result_parameter_name=parent_result_parameter_name,
                return_func_results=return_func_results,
                with_output_dataset=with_output_dataset,
                output_file=output_file,
                output_dataset=output_dataset,
                num_events=num_events,
                num_events_per_job=num_events_per_job,
                with_input_datasets=with_input_datasets,
                input_datasets=input_datasets,
            )
        elif self.job_type == JobType.SCRIPT:
            job = Job(
                job_id=job_id,
                job_type=job_type,
                script_path=script_path,
                params=new_params,
                working_dir=self.working_dir,
                output_files=["result.json"],
                parent_result_parameter_name=parent_result_parameter_name,
            )
        elif self.job_type == JobType.CONTAINER:
            job = Job(
                job_id=job_id,
                job_type=job_type,
                container_image=container_image,
                container_command=container_command,
                params=new_params,
                working_dir=self.working_dir,
                output_files=["result.json"],
                parent_result_parameter_name=parent_result_parameter_name,
            )
        else:
            raise ValueError(f"Unsupported job type: {self.job_type}")

        job.set_runner(runner)
        return job

    def get_key_from_dict(self, key: Any) -> Union[str, tuple]:
        """
        Get key from a dict.

        Args:
            key: dictionary key.
        """
        if not key:
            return "None"
        return tuple(sorted(key.items()))

    def _initialize(self) -> None:
        """
        Initialize MultiStepsJobs from MultiStepsFunction.
        """
        objective_funcs = self.function.objective_funcs
        deps = self.function.deps
        if self.function.global_parameters:
            self.logger.info(f"func global parameters: {self.function.global_parameters}")
            g_parameters = self.function.global_parameters

            sorted_keys = sorted(g_parameters.keys())
            combinations = [dict(zip(sorted_keys, values)) for values in product(*[g_parameters[k] for k in sorted_keys])]
            self.global_parameters = combinations
        self.global_parameters_steps = self.function.global_parameters_steps

        for step_name in objective_funcs:
            func = objective_funcs[step_name].get("func", None)
            script_path = objective_funcs[step_name].get("script_path", None)
            container_image = objective_funcs[step_name].get("container_image", None)
            container_command = objective_funcs[step_name].get("container_command", None)
            job_type = objective_funcs[step_name].get("job_type", JobType.FUNCTION)
            parent_result_parameter_name = objective_funcs[step_name].get("parent_result_parameter_name", None)

            return_func_results = objective_funcs[step_name].get("return_func_results", True)
            with_output_dataset = objective_funcs[step_name].get("with_output_dataset", False)
            output_file = objective_funcs[step_name].get("output_file", None)
            orig_output_dataset = objective_funcs[step_name].get("output_dataset", None)
            num_events = objective_funcs[step_name].get("num_events", 1)
            num_events_per_job = objective_funcs[step_name].get("num_events_per_job", 1)

            with_input_datasets = objective_funcs[step_name].get("with_input_datasets", False)
            orig_input_datasets = objective_funcs[step_name].get("input_datasets", None)

            runner = objective_funcs[step_name]["runner"]
            if not runner:
                runner = self.runner

            self.step_states[step_name] = {"state": JobState.NEW, "return_func_results": return_func_results}
            if not self.global_parameters or step_name not in self.global_parameters_steps:
                output_dataset = orig_output_dataset
                input_datasets = copy.deepcopy(orig_input_datasets)
                if orig_output_dataset:
                    output_dataset = orig_output_dataset.replace("#global_parameter_key", "None").replace("#trial_id", self.trial_id).replace("#job_id", self.job_id)
                else:
                    output_dataset = orig_output_dataset
                if orig_input_datasets:
                    input_datasets = copy.deepcopy(orig_input_datasets)
                    for k in input_datasets.keys():
                        input_datasets[k] = input_datasets[k].replace("#global_parameter_key", "None").replace("#trial_id", self.trial_id).replace("#job_id", self.job_id)
                else:
                    input_datasets = orig_input_datasets

                step_job = self.get_step_job(
                    job_type,
                    runner,
                    func=func,
                    additional_parameters=None,
                    script_path=script_path,
                    container_image=container_image,
                    container_command=container_command,
                    parent_result_parameter_name=parent_result_parameter_name,
                    return_func_results=return_func_results,
                    with_output_dataset=with_output_dataset,
                    output_file=output_file,
                    output_dataset=output_dataset,
                    num_events=num_events,
                    num_events_per_job=num_events_per_job,
                    with_input_datasets=with_input_datasets,
                    input_datasets=input_datasets,
                )
                g_params = self.get_key_from_dict(None)
                self.step_jobs[step_name] = {g_params: step_job}
            else:
                self.step_jobs[step_name] = {}
                for g_params in self.global_parameters:
                    g_param_str = "+".join(f"{k}_{v}" for k, v in sorted(g_params.items()))
                    g_param_str = g_param_str.replace("+", "plus")
                    g_param_str = g_param_str.replace("-", "minus")
                    if orig_output_dataset:
                        output_dataset = orig_output_dataset.replace("#global_parameter_key", g_param_str).replace("#trial_id", self.trial_id).replace("#job_id", self.job_id)
                    else:
                        output_dataset = orig_output_dataset
                    if orig_input_datasets:
                        input_datasets = copy.deepcopy(orig_input_datasets)
                        for k in input_datasets.keys():
                            input_datasets[k] = input_datasets[k].replace("#global_parameter_key", g_param_str).replace("#trial_id", self.trial_id).replace("#job_id", self.job_id)
                    else:
                        input_datasets = orig_input_datasets

                    step_job = self.get_step_job(
                        job_type,
                        runner,
                        func=func,
                        additional_parameters=g_params,
                        script_path=script_path,
                        container_image=container_image,
                        container_command=container_command,
                        parent_result_parameter_name=parent_result_parameter_name,
                        return_func_results=return_func_results,
                        with_output_dataset=with_output_dataset,
                        output_file=output_file,
                        output_dataset=output_dataset,
                        num_events=num_events,
                        num_events_per_job=num_events_per_job,
                        with_input_datasets=with_input_datasets,
                        input_datasets=input_datasets,
                    )
                    g_params_key = self.get_key_from_dict(g_params)
                    self.step_jobs[step_name][g_params_key] = step_job
        self.deps = {}
        if deps:
            for dep in deps:
                if type(deps[dep]) in [str]:
                    self.deps[dep] = {
                        "parent": deps[dep],
                        "state": JobState.NEW,
                        "dep_type": "results",
                        "dep_map": "one2one",
                    }
                elif type(deps[dep]) in [dict]:
                    self.deps[dep] = {
                        "parent": deps[dep]["parent"],
                        "state": JobState.NEW,
                        "dep_type": deps[dep].get("dep_type", "results"),
                        "dep_map": deps[dep].get("dep_map", "one2one")
                    }

        if not self.final:
            for step_name in self.step_jobs:
                # last step_name
                self.final = step_name

        self.logger.info(f"Job {self.job_id} is initialized: step_jobs: {self.step_jobs}, deps: {self.deps}, final: {self.final}")
        self.logger.info(f"Job {self.job_id} is initialized: global parameters: {self.global_parameters}, global parameter steps: {self.global_parameters_steps}")

    def get_ready_steps(self) -> list:
        """
        Get steps that are ready to run.
        """
        if self.state in [JobState.COMPLETED, JobState.FAILED]:
            return {}

        readys = []
        for step_name in self.step_jobs:
            if (step_name not in self.deps or self.deps[step_name].get("state", JobState.NEW) == JobState.READY) and (self.step_states[step_name]["state"] in [JobState.NEW]):
                # self.step_jobs[step_name].state not in [JobState.COMPLETED, JobState.FAILED, JobState.RUNNING, JobState.PAUSED, JobState.CANCELLED]:
                readys.append(step_name)
        return readys

    def set_runner(self, runner) -> None:
        """
        Set the runner for this job.

        Args:
            runner: The runner to use for this job
        """
        self.runner = runner

    def set_internal_id(self, internal_id) -> None:
        """
        Set internal id for the job.

        Args:
            internal_id: The internal id for the job.
        """
        self.internal_id = internal_id

    def set_parent_results(self, step, job_key, results) -> None:
        """
        Set results for the parent job.

        Args:
            step: The step name of the curret job
            job_key: The job key of the curret job
            results: Results from the parent job
        """
        self.logger.info(f"Set parent results for job {self.job_id} step {step} job_key {job_key}: {results}")
        self.parent_results = results
        if self.parent_result_parameter_name and results:
            old_params = copy.deepcopy(self.params)
            self.params[self.parent_result_parameter_name] = results.get(self.parent_result_parameter_name, None)
            self.logger.info(f"Change parameters for job {self.job_id} step {step} job_key {job_key} from {old_params} to {self.params}")

    def get_parent_results(self, step_job, step_name, g_param_key) -> (bool, object):
        """
        Get parent results for a step job.

        Args:
            step_job: The current job
            step_name: The current step name.
            g_param_key: The current step key.
        """
        self.logger.info(f"Get parent results for step {step_name} job key {g_param_key}")
        if step_name not in self.deps:
            self.logger.info(f"No parent dependency for step {step_name} job key {g_param_key}")
            return False, None

        parent = self.deps[step_name].get("parent", None)
        dep_type = self.deps[step_name].get("dep_type", "results")
        dep_map = self.deps[step_name].get("dep_map", "one2one")
        parent_jobs = self.step_jobs.get(parent, {})
        self.logger.info(f"For step {step_name} job key {g_param_key}: parent {parent}, dep_type {dep_type}, dep_map {dep_map}, parent_jobs: {parent_jobs}")

        if dep_type in ["datasets"]:
            # depend on the rucio dataset name
            if dep_map != "one2one":
                dep_map == "one2one"
                self.logger.info(f"For step {step_name} job key {g_param_key}, dep_type is datasets. the dep_map forced to one2one")

            parent_job = parent_jobs.get(g_param_key, None)
            if not parent_job:
                err = f"For step {step_name} job key {g_param_key} with dep map {dep_map}, no parent jobs are found for job key {g_param_key}"
                self.logger.error(err)
                raise Exception(err)

            step_job.parent_internal_id = parent_job.internal_id
            return False, None
        if not parent_jobs:
            # not parent jobs
            return False, None
        if dep_map == "one2one":
            parent_job = parent_jobs.get(g_param_key, None)
            if not parent_job:
                err = f"For step {step_name} job key {g_param_key} with dep map {dep_map}, no parent jobs are found for job key {g_param_key}"
                self.logger.error(err)
                raise Exception(err)

            results = parent_job.results
            return True, results
        elif dep_map == "all2one":
            results = defaultdict(dict)
            for job_key, job in parent_jobs.items():
                for metric, value in job.results.items():
                    results[metric][job_key] = value

            # Optionally convert back to regular dict
            results = dict(results)
            return True, results
        return None

    def run_ready_steps(self) -> None:
        """
        Run ready steps
        """
        ready_steps = self.get_ready_steps()
        if ready_steps:
            self.logger.info(f"Ready to run steps: {ready_steps}")
        for step in ready_steps:
            for g_param_key in self.step_jobs[step]:
                step_job = self.step_jobs[step][g_param_key]
                has_parent, parent_results = self.get_parent_results(step_job, step, g_param_key)
                if has_parent:
                    step_job.set_parent_results(step, g_param_key, parent_results)
                self.logger.info(f"Ready to run job {step_job.job_id} step {step} job_key {g_param_key}")
                step_job.run()
            if self.step_states[step]["return_func_results"]:
                self.step_states[step]["state"] = JobState.RUNNING
            else:
                self.step_states[step]["state"] = JobState.RUNNINGNOMONITOR

    def run(self) -> None:
        """
        Run this job using its assigned runner.
        """
        self.state = JobState.RUNNING
        self.start_time = datetime.now()
        self.run_ready_steps()

    def get_final_results(self) -> None:
        """
        Get the final step's results and assign it to the MultiStepJob.
        """
        self.logger.info(f"Getting final results for Job {self.job_id}")
        if self.step_states[self.final]["state"] not in [JobState.COMPLETED, JobState.FAILED]:
            return
        g_param_keys = list(self.step_jobs[self.final].keys())
        if len(g_param_keys) != 1:
            error = f"Job {self.job_id} should have only one job to get results. However it has different jobs {g_param_keys}"
            self.logger.error(error)
            self.fail({"error": error})
        g_param_key = g_param_keys[0]
        self.results = self.step_jobs[self.final][g_param_key].results
        self.logger.info(f"Job {self.job_id} set results from step {self.final} g_param_key {g_param_key} job {self.step_jobs[self.final][g_param_key].job_id}")

    def check_status(self) -> None:
        """
        Run to check the status of the job.
        """
        if self.state in [JobState.NEW, JobState.READY, JobState.CREATED, JobState.COMPLETED, JobState.FAILED]:
            return

        # check the steps
        has_failures = False
        for step_name in self.step_jobs:
            for g_param_key in self.step_jobs[step_name]:
                if not self.step_jobs[step_name][g_param_key].return_func_results:
                    continue
                self.step_jobs[step_name][g_param_key].check_status()
                if self.step_jobs[step_name][g_param_key].has_failed():
                    self.logger.error(f"Job {self.job_id} failed at step {step_name} with global_parameters {g_param_key}")
                    has_failures = True
        if has_failures:
            for step_name in self.step_jobs:
                for g_param_key in self.step_jobs[step_name]:
                    self.step_jobs[step_name][g_param_key].cancel()
                    self.logger.error(f"Job {self.job_id} has failures, cancel step {step_name} with global_parameters {g_param_key}")
            self.logger.info(f"Set Job {self.job_id} failed")
            self.fail({"error": f"Job {self.job_id} has failures"})
            return

        for step_name in self.step_jobs:
            if all(self.step_jobs[step_name][g_param_key].is_completed()for g_param_key in self.step_jobs[step_name]):
                self.logger.info(f"Job {self.job_id} step {step_name} completed")
                self.step_states[step_name]["state"] = JobState.COMPLETED
            elif any(self.step_jobs[step_name][g_param_key].has_failed()for g_param_key in self.step_jobs[step_name]):
                self.logger.info(f"Job {self.job_id} step {step_name} has failed")
                self.step_states[step_name]["state"] = JobState.FAILED

        # if the final step terminates, terminate the job
        if self.step_states[self.final]["state"] in [JobState.COMPLETED]:
            self.get_final_results()
            self.complete(self.results)
            return
        elif self.step_states[self.final]["state"] in [JobState.FAILED]:
            self.get_final_results()
            self.fail(self.results)
            return

        # check the dependencies
        for dep in self.deps:
            if self.deps[dep]["state"] not in [JobState.READY]:
                parent = self.deps[dep]["parent"]
                if self.step_states[parent]["state"] in [JobState.COMPLETED, JobState.FAILED, JobState.RUNNINGNOMONITOR]:
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
