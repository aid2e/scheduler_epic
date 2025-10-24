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
        self.metrics: Dict[str, Any] = {}
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
        # return tuple(sorted(key.items()))
        return ",".join(f"{k}={key[k]}" for k in sorted(key))

    def is_multi_objectives_in_one_step(self, step_name, step) -> bool:
        """
        To check whether multiple objectives in one step.

        # This one has only one objective in step1.
        objective_funcs={
            "step1": {
                "func": objective_function1,
                "job_type": JobType.FUNCTION,
                "runner": panda_runner,
            },
        }

        # This one has multiple objectives in step1.
        objective_funcs={
            "step1": {
                "objective1": {
                    "func": objective_function1,
                    "job_type": JobType.FUNCTION,
                    "runner": panda_runner,
                },
                "objective2": {
                    "func": objective_function1,
                    "job_type": JobType.FUNCTION,
                    "runner": panda_runner,
                },
            },
        }

        Args:
            step_name: The step name
            step: The step function structure
        """
        if type(step) in [dict]:
            for k in step:
                if type(step[k]) in [dict] and "func" in step[k]:
                    return True
        return False

    def _init_step_objective_job(self, step_objective, step_name) -> (Dict[str, Job], bool):
        """
        Initialize objective job.

        Args:
            step_objective: The step objective
            step_name: The step name

        Returns:
            Dictionay of jobs (objective, Job)
            return_func_results as bool
        """
        func = step_objective.get("func", None)
        script_path = step_objective.get("script_path", None)
        container_image = step_objective.get("container_image", None)
        container_command = step_objective.get("container_command", None)
        job_type = step_objective.get("job_type", JobType.FUNCTION)
        parent_result_parameter_name = step_objective.get("parent_result_parameter_name", None)

        # always set return_func_results, so that the metrics can be retrieved
        # return_func_results = step_objective.get("return_func_results", True)
        return_func_results = True
        with_output_dataset = step_objective.get("with_output_dataset", False)
        output_file = step_objective.get("output_file", None)
        orig_output_dataset = step_objective.get("output_dataset", None)
        num_events = step_objective.get("num_events", 1)
        num_events_per_job = step_objective.get("num_events_per_job", 1)

        with_input_datasets = step_objective.get("with_input_datasets", False)
        orig_input_datasets = step_objective.get("input_datasets", None)

        runner = step_objective.get("runner", None)
        if not runner:
            runner = self.runner

        step_jobs = {}
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
            step_jobs = {g_params: step_job}
        else:
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
                step_jobs[g_params_key] = step_job
        return step_jobs, return_func_results

    def _init_step_jobs(self, objective_funcs, step_name) -> None:
        """
        Initialize objective job.

        Args:
            objective_funcs: Objective functions
            step_name: The step name
        """
        is_mul_objs = self.is_multi_objectives_in_one_step(step_name, objective_funcs[step_name])
        if not is_mul_objs:
            objective = "None"
            step_objective = objective_funcs[step_name]
            step_jobs, return_func_results = self._init_step_objective_job(step_objective, step_name)
            self.step_jobs[step_name] = {objective: step_jobs}
            self.step_states[step_name] = {
                "state": JobState.NEW,
                "is_mul_objectives": is_mul_objs,
                "with_global_parameters": self.global_parameters and step_name in self.global_parameters_steps,
                "return_func_results": return_func_results,
                "results": {},
                "step_results": {},
                "metrics": {}
            }
        else:
            step_objectives = objective_funcs[step_name]
            self.step_jobs[step_name] = {}
            all_return_func_results = False
            for objective in step_objectives:
                step_jobs, return_func_results = self._init_step_objective_job(step_objectives[objective], step_name)
                self.step_jobs[step_name][objective] = step_jobs
                if return_func_results:
                    all_return_func_results = True
            self.step_states[step_name] = {
                "state": JobState.NEW,
                "is_mul_objectives": is_mul_objs,
                "with_global_parameters": self.global_parameters and step_name in self.global_parameters_steps,
                "return_func_results": all_return_func_results,
                "results": {},
                "step_results": {},
                "metrics": {}
            }

    def _initialize(self) -> None:
        """
        Initialize MultiStepsJobs from MultiStepsFunction.
        """
        objective_funcs = self.function.objective_funcs
        deps = self.function.deps
        if self.function.global_parameters:
            self.logger.info(f"func global parameters: {self.function.global_parameters}")
            if type(self.function.global_parameters) in [list, tuple]:
                self.global_parameters = copy.deepcopy(self.function.global_parameters)
            else:
                g_parameters = self.function.global_parameters

                sorted_keys = sorted(g_parameters.keys())
                combinations = [dict(zip(sorted_keys, values)) for values in product(*[g_parameters[k] for k in sorted_keys])]
                self.global_parameters = combinations
        self.global_parameters_steps = self.function.global_parameters_steps

        for step_name in objective_funcs:
            self._init_step_jobs(objective_funcs, step_name)

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

    def get_parent_results(self, step_job, step_name, objective, g_param_key) -> (bool, object):
        """
        Get parent results for a step job.

        Args:
            step_job: The current job
            step_name: The current step name
            objective: The objective
            g_param_key: The current step key
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
                self.logger.info(f"For step {step_name} job key {g_param_key}, dep_type is datasets. the dep_map is forced to one2one")

            parent_job = parent_jobs.get(objective, {}).get(g_param_key, None)
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
            parent_job = parent_jobs.get(objective, {}).get(g_param_key, None)
            if not parent_job:
                err = f"For step {step_name} job key {g_param_key} with dep map {dep_map}, no parent jobs are found for job key {g_param_key}"
                self.logger.error(err)
                raise Exception(err)

            results = parent_job.results
            return True, results
        elif dep_map == "all2one":
            results = defaultdict(dict)
            for job_key, job in parent_jobs.get(objective, {}).items():
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
            for objective in self.step_jobs[step]:
                for g_param_key in self.step_jobs[step][objective]:
                    step_job = self.step_jobs[step][objective][g_param_key]
                    has_parent, parent_results = self.get_parent_results(step_job, step, objective, g_param_key)
                    if has_parent:
                        step_job.set_parent_results(step, objective, g_param_key, parent_results)
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
        if self.results is None:
            self.results = {}
        objectives = list(self.step_jobs[self.final].keys())
        for objective in objectives:
            g_param_keys = list(self.step_jobs[self.final][objective].keys())
            if len(g_param_keys) != 1:
                error = f"Job {self.job_id} should have only one job to get results. However it has different jobs {g_param_keys}"
                self.logger.error(error)
                self.fail({"error": error})
            g_param_key = g_param_keys[0]
            results = self.step_jobs[self.final][objective][g_param_key].results
            self.logger.info(f"Job {self.job_id} update results from step {self.final} objective {objective} g_param_key {g_param_key} job {self.step_jobs[self.final][objective][g_param_key].job_id}")
            self.results.update(results)

    def get_objective_results(self, objective_jobs, with_global_parameters=False) -> Dict:
        """
        Get results for an objective with multiple global parameter keys

        Args:
            objective_jobs: Dictionary of (global_parameter_key, Job)
            with_global_parameters: whether it has global parameters

        Returns:
            results with different metrics
        """
        try:
            self.logger.debug(f"get_objective_results with_global_parameters: {with_global_parameters}, objective_jobs: {objective_jobs}")
            if with_global_parameters:
                results = defaultdict(dict)
                metrics = {}
                for job_key, job in objective_jobs.items():
                    for metric, value in job.results.items():
                        results[metric][job_key] = value
                    metrics[job_key] = job.get_metrics()
            else:
                if len(list(objective_jobs.keys())) > 1:
                    error = f"objective_jobs {objective_jobs} has more than one global parameter key. However, with_global_parameters is {with_global_parameters}"
                    self.logger.error(error)
                    self.fail({"error": error})
                results = list(objective_jobs.values())[0].results
                metrics = list(objective_jobs.values())[0].get_metrics()
            return results, metrics
        except Exception as ex:
            self.logger.error(f"get_objective_results raise exceptions: {ex}")
        return None, None

    def get_step_results(self, objective_results) -> Dict:
        """
        Get results for a step with multiple objectives

        Args:
            objective_results: Dictionary of (metric, value)

        Returns:
            results with different metrics
        """
        results = {}
        for objective in objective_results:
            results.update(objective_results[objective])
        return results

    def check_status(self) -> None:
        """
        Run to check the status of the job.
        """
        if self.state in [JobState.NEW, JobState.READY, JobState.CREATED, JobState.COMPLETED, JobState.FAILED]:
            return

        # check the steps
        has_failures = False
        for step_name in self.step_jobs:
            for objective in self.step_jobs[step_name]:
                for g_param_key in self.step_jobs[step_name][objective]:
                    if not self.step_jobs[step_name][objective][g_param_key].return_func_results:
                        self.step_jobs[step_name][objective][g_param_key].check_status()
                        continue
                    self.step_jobs[step_name][objective][g_param_key].check_status()
                    if self.step_jobs[step_name][objective][g_param_key].has_failed():
                        self.logger.error(f"Job {self.job_id} failed at step {step_name} objective {objective} with global_parameters {g_param_key}")
                        has_failures = True
        if has_failures:
            for step_name in self.step_jobs:
                for objective in self.step_jobs[step_name]:
                    for g_param_key in self.step_jobs[step_name][objective]:
                        self.step_jobs[step_name][objective][g_param_key].cancel()
                        self.logger.error(f"Job {self.job_id} has failures, cancel step {step_name} objective {objective} with global_parameters {g_param_key}")
            self.logger.info(f"Set Job {self.job_id} failed")
            self.fail({"error": f"Job {self.job_id} has failures"})
            return

        for step_name in self.step_jobs:
            all_completed = True
            step_failed = False

            for objective in self.step_jobs[step_name]:
                objective_jobs = self.step_jobs[step_name][objective]
                completed = all(job.is_completed() for job in objective_jobs.values())
                failed = any(job.has_failed() for job in objective_jobs.values())

                if completed:
                    self.logger.info(f"Job {self.job_id} step {step_name} objective {objective} completed")
                    # retrieve results
                    obj_results, obj_metrics = self.get_objective_results(objective_jobs, with_global_parameters=self.step_states[step_name]["with_global_parameters"])
                    if not obj_results:
                        step_failed = True
                    self.step_states[step_name]["results"][objective] = obj_results
                    self.step_states[step_name]["metrics"][objective] = obj_metrics
                    self.logger.info(f"Job {self.job_id} step {step_name} objective {objective} results {obj_results}, metrics: {obj_metrics}")
                elif failed:
                    self.logger.info(f"Job {self.job_id} step {step_name} objective {objective} has failed")
                    obj_results, obj_metrics = self.get_objective_results(objective_jobs, with_global_parameters=self.step_states[step_name]["with_global_parameters"])
                    self.step_states[step_name]["results"][objective] = obj_results
                    self.step_states[step_name]["metrics"][objective] = obj_metrics
                    self.logger.info(f"Job {self.job_id} step {step_name} failed, objective {objective} results {obj_results}, metrics: {obj_metrics}")
                    step_failed = True
                else:
                    all_completed = False  # Still waiting on jobs to complete

            if step_failed:
                self.step_states[step_name]["state"] = JobState.FAILED
            elif all_completed:
                self.step_states[step_name]["state"] = JobState.COMPLETED
                step_results = self.get_step_results(self.step_states[step_name]["results"])
                self.logger.info(f"Job {self.job_id} step {step_name} completed")
                self.logger.info(f"Job {self.job_id} step {step_name} results {step_results}")

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
        metrics = defaultdict(dict)
        for step_name in self.step_jobs:
            for objective in self.step_jobs[step_name]:
                r_metrics = self.step_states[step_name]["metrics"][objective]
                self.logger.debug(f"Job {self.job_id} step {step_name} objective {objective} metrics: {r_metrics}")
                metrics[step_name][objective] = r_metrics
        self.metrics.update(metrics)
        self.logger.debug(f"Job {self.job_id} metrics: {self.metrics}")
        return self.metrics
