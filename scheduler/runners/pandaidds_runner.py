"""
PanDARunner - Runner that submits jobs to the PanDA system.
"""

import datetime
import logging
import os
from itertools import product
from typing import Dict, Any
from ..job.job import Job
from ..job.job_state import JobState
from ..job.multi_steps_job import MultiStepsJob
from .base_runner import BaseRunner


def empty_workflow_func():
    pass


class PanDAiDDSRunner(BaseRunner):
    """
    A runner that submits jobs to the PanDA system.

    This runner requires the PanDA client to be installed.
    """

    def __init__(
        self,
        name: str = None,
        cloud: str = "US",
        queue: str = "BNL_PanDA_1",
        vo: str = "wlcg",
        init_env: str = None,
        source_dir: str = None,
        source_dir_parent_level: int = 1,
        exclude_source_files: list = [],
        max_walltime: int = 36000,
        core_count: int = 1,
        total_memory: int = 4000,
        enable_separate_log: bool = True,
        global_parameters: dict = {},
        job_dir: str = None,
        funcs: dict = {},
        deps: dict = {},
        config: Dict[str, Any] = None,
    ):
        """
        Initialize a new PanDAiDDSRunner.

        Args:
            site: Site to submit jobs to
            cloud: Cloud to submit jobs to
            queue: Queue to submit jobs to
            vo: Virtual organization
            config: Additional configuration options
        """
        super().__init__(config or {})

        self.name = name
        self.cloud = cloud
        self.queue = queue
        self.vo = vo
        self.init_env = init_env
        self.source_dir = source_dir
        self.source_dir_parent_level = source_dir_parent_level
        self.exclude_source_files = exclude_source_files
        self.max_walltime = max_walltime
        self.core_count = core_count
        self.total_memory = total_memory
        self.enable_separate_log = enable_separate_log
        self.global_parameters = global_parameters
        self.config = config

        self.jobs = {}  # job_id -> panda_job_id

        # Directory to store job files
        self.job_dir = job_dir or os.path.expanduser("~/panda_jobs")
        os.makedirs(self.job_dir, exist_ok=True)

        self.funcs = funcs
        self.deps = deps
        self.running_funcs = {}
        self.ordered_funcs = self.order_funcs(self.funcs, self.deps)

        self.logger = logging.getLogger("PanDAiDDSRunner")

        self.num_checks = 0
        self.workflow = None
        self.workflow_id = None

    def order_funcs(self, funcs, deps):
        ordered_funcs = []
        funcs_keys = funcs.keys()
        while funcs_keys:
            for name in funcs_keys:
                if name not in deps:
                    ordered_funcs.append(name)
                if deps[name] in ordered_funcs:
                    ordered_funcs.append(name)
            for name in ordered_funcs:
                funcs_keys.pop(name)
        return ordered_funcs

    def submit_workflow(self, job) -> object:
        # import iDDS workflow
        from idds.iworkflow.workflow import workflow as workflow_def  # workflow    # noqa F401

        if self.workflow is None:
            workflow_name = f'{self.name}.{datetime.datetime.now().strftime("%Y%m%d_%H_%S")}'
            self.logger.info(f"Defining workflow for experiment {workflow_name}")
            # define the workflow
            workflow = workflow_def(
                func=empty_workflow_func,
                name=workflow_name,
                service="panda",
                cloud=self.cloud,
                queue=self.queue,
                init_env=self.init_env,
                source_dir=self.source_dir,
                source_dir_parent_level=self.source_dir_parent_level,
                exclude_source_files=self.exclude_source_files,
                max_walltime=self.max_walltime,
                core_count=self.core_count,
                total_memory=self.total_memory,
                enable_separate_log=self.enable_separate_log,
                local=True,
                return_workflow=True,
            )()

            workflow.pre_run()
            workflow.prepare()
            req_id = workflow.submit()
            self.logger.info(f"Workflow id for experiment {workflow_name}: {req_id}")
            if not req_id:
                raise Exception(f"Failed to submit workflow for experiment {workflow_name} to PanDA")

            self.workflow = workflow
            self.workflow_id = req_id
        return self.workflow

    def submit_job(self, job) -> None:
        from idds.iworkflow.work import work as work_def

        workflow = self.submit_workflow(job)

        func = job.function
        func_name = func.__name__

        work_name = f"{self.name}.{job.job_id}.{func_name}"
        g_param_str = "None"
        self.logger.info(f"Defining work {work_name}")

        self.running_funcs[job.job_id] = {"funcs": {}}

        if func_name not in g_param_str not in self.running_funcs[job.job_id]["funcs"]:
            self.running_funcs[job.job_id]["funcs"][func_name] = {}

        if g_param_str not in self.running_funcs[job.job_id]["funcs"][func_name]:
            if job.with_output_dataset:
                output_dataset_name = job.output_dataset
                if not output_dataset_name.endswith("/"):
                    output_dataset_name = output_dataset_name + "/"
                work = work_def(
                    func=func,
                    workflow=workflow,
                    return_work=True,
                    map_results=True,
                    name=work_name,
                    job_key=work_name,
                    log_dataset_name=f"{work_name}.log/",
                    output_file_name=job.output_file,
                    output_dataset_name=output_dataset_name,
                    num_events=job.num_events,
                    num_events_per_job=job.num_events_per_job,
                    parent_internal_id=job.parent_internal_id,
                )(**job.params)
            elif job.with_input_datasets:
                work = work_def(
                    func=func,
                    workflow=workflow,
                    return_work=True,
                    map_results=True,
                    name=work_name,
                    job_key=work_name,
                    log_dataset_name=f"{work_name}.log/",
                    input_datasets=job.input_datasets,
                    parent_internal_id=job.parent_internal_id,
                )(**job.params)
            else:
                work = work_def(
                    func=func,
                    workflow=workflow,
                    return_work=True,
                    map_results=True,
                    name=work_name,
                    job_key=work_name,
                    log_dataset_name=f"{work_name}.log/",
                    parent_internal_id=job.parent_internal_id,
                )(**job.params)

            job.set_internal_id(work.internal_id)

            tf_id = work.submit()
            self.logger.info(f"Submit work {work_name} internal_id {work.internal_id} to PanDA/iDDS with transform_id {tf_id}, parent_internal_id {work.parent_internal_id}")
            if not tf_id:
                raise Exception(f"Failed to submit {work_name} to PanDA")

            if job.return_func_results:
                work.init_async_result()

            self.running_funcs[job.job_id]["funcs"][func_name][g_param_str] = {
                "work": work,
                "tf_id": tf_id,
                "status": "New",
                "return_func_results": job.return_func_results,
                "results": None,
                "job_key": work_name,
            }
        else:
            if job.return_func_results:
                self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["work"].init_async_result()

    def submit_multi_steps_job(self, job) -> None:
        from idds.iworkflow.work import work as work_def

        workflow = self.submit_workflow(job)

        # different tasks based on the global parameters
        g_params = [dict(zip(self.global_parameters.keys(), values)) for values in product(*self.global_parameters.values())]
        self.logger.info(f"global parameters: {g_params}")

        # define works
        self.logger.info(f"defining works for ordered funcs: {self.ordered_funcs}")
        for func_name in self.ordered_funcs:
            func = self.funcs[func_name].get("func")
            output_file = self.funcs[func_name].get("output_file", None)
            input_files = self.funcs[func_name].get("input_files", None)
            output_dataset = self.funcs[func_name].get("output_dataset", None)
            input_datasets = self.funcs[func_name].get("input_datasets", None)
            return_func_results = self.funcs[func_name].get("return_func_results", False)
            num_events = self.funcs[func_name].get("num_events")
            num_events_per_job = self.funcs[func_name].get("num_events_per_job")
            parent_func_name = self.deps.get(func_name)

            self.running_funcs[job.job_id]["funcs"][func_name] = {}

            if g_params:
                my_funcs = self.running_funcs[job.job_id]["funcs"]

                for g_param in g_params:
                    g_param_str = "+".join(f"{k}_{v}" for k, v in g_param.items())
                    if g_param_str not in my_funcs[func_name]:
                        work_name = f"{self.name}.{job.job_id}.{func_name}.{g_param_str}"
                        work = work_def(
                            func=func,
                            workflow=workflow,
                            return_work=True,
                            map_results=True,
                            name=work_name,
                            output_file_name=output_file,
                            output_dataset_name=(f"{output_dataset}.{job.job_id}" if output_dataset else None),
                            num_events=num_events,
                            num_events_per_job=num_events_per_job,
                            input_datasets=dict(zip(input_files, input_datasets)),
                            log_dataset_name=(f"{output_dataset}.{job.job_id}.log" if output_dataset else f"{work_name}.log"),
                            parent_transform_id=(self.running_funcs[parent_func_name].get("tf_id", None) if parent_func_name else None),
                            parent_internal_id=(self.running_funcs[parent_func_name].get("work").internal_id if parent_func_name else None),
                            job_key=work_name,
                        )

                        tf_id = work.submit()
                        if not tf_id:
                            raise Exception(f"failed to submit {work_name} to PanDA")

                        if return_func_results:
                            work.init_async_result()

                        self.running_funcs[job.job_id]["funcs"][func_name][g_param_str] = {
                            "work": work(**job.parameters, **g_params),
                            "tf_id": tf_id,
                            "status": "New",
                            "return_func_results": return_func_results,
                            "results": None,
                            "job_key": work_name,
                        }
                    else:
                        if return_func_results:
                            self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["work"].init_async_result()
            else:
                work_name = f"{self.name}.{job.job_id}.{func_name}"
                g_param_str = "None"
                if g_param_str not in self.running_funcs[job.job_id]["funcs"][func_name]:
                    work = work_def(
                        func=func,
                        workflow=self.workflow,
                        return_work=True,
                        map_results=True,
                        name=work_name,
                        output_file_name=output_file,
                        output_dataset_name=(f"{output_dataset}.{job.job_id}" if output_dataset else None),
                        num_events=num_events,
                        num_events_per_job=num_events_per_job,
                        input_dataset=dict(zip(input_files, input_datasets)),
                        log_dataset_name=(f"{output_dataset}.{job.job_id}.log" if output_dataset else f"{work_name}.log"),
                        parent_transform_id=(self.running_funcs[parent_func_name].get("tf_id", None) if parent_func_name else None),
                        parent_internal_id=(self.running_funcs[parent_func_name].get("work").internal_id if parent_func_name else None),
                        job_key=work_name,
                    )

                    tf_id = work.submit()
                    if not tf_id:
                        raise Exception(f"failed to submit {work_name} to PanDA")

                    if return_func_results:
                        work.init_async_result()

                    self.running_funcs[job.job_id]["funcs"][func_name][g_param_str] = {
                        "work": work(*job.parameters, **g_params),
                        "tf_id": tf_id,
                        "status": "New",
                        "return_func_results": return_func_results,
                        "results": None,
                        "job_key": work_name,
                    }
                else:
                    if return_func_results:
                        self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["work"].init_async_result()

    def run_job(self, job) -> None:
        """
        Run a job using the appropriate execution method.

        Args:
            job: The job to run
        """
        if type(job) in [Job]:
            self.submit_job(job)
        else:
            # type(job) in [MulJob]:
            self.submit_multi_steps_job(job)

    def check_single_job_status(self, job) -> None:
        """
        Check the status of a single job and update its state.

        Args:
            job: The job to check
        """

        func = job.function
        func_name = func.__name__

        # work_name = f"{self.name}.{job.job_id}.{func_name}"
        g_param_str = "None"
        # return_func_results = self.funcs[job.job_id]["funcs"][func_name].get("return_func_results", False)
        work = self.running_funcs[job.job_id]["funcs"].get(func_name, {}).get(g_param_str, {}).get("work", None)
        tf_id = self.running_funcs[job.job_id]["funcs"].get(func_name, {}).get(g_param_str, {}).get("tf_id", None)

        if not work or not tf_id:
            err = f"Job {job.job_id} has no work {work} or no tf_id {tf_id}"
            self.logger.error(err)
            # return
            raise Exception(err)

        work.init_async_result()
        status = work.get_status()
        if work.is_finished(status):
            self.logger.info(f"Job {job.job_id} with transform_id {tf_id} finished")

            ret = work.get_results()
            job_key = self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["job_key"]
            results = ret.get_result(name=work.name, key=job_key, verbose=True)
            self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["results"] = results
            self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["status"] = "finished"
            if job.state != JobState.COMPLETED:
                self.logger.info(f"Job {job.job_id} with transform_id {tf_id} complete with results: {results}")
                job.complete(results)
            self.running_funcs.pop(job.job_id, None)
        elif work.is_failed(status):
            self.logger.info(f"Job {job.job_id} with transform_id {tf_id} failed")

            self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["status"] = "failed"
            job.fail(f"Failed to execute {func_name} with transform_id {tf_id}")
            self.running_funcs.pop(job.job_id, None)

    def check_multi_steps_job_status(self, job) -> None:
        """
        Check the status of a multi_steps_job and update its state.

        Args:
            job: The job to check
        """
        # check job status
        for func_name in self.running_funcs[job.job_id]["funcs"]:
            return_func_results = self.funcs[job.job_id]["funcs"][func_name].get("return_func_results", False)
            if return_func_results:
                for g_param_str in self.running_funcs[job.job_id]["funcs"][func_name]:
                    work = self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["work"]

                    work.init_async_result()
                    if work.is_finished():
                        ret = work.get_results()
                        job_key = self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["job_key"]
                        results = ret.get_result(nam=work.name, key=job_key, verbose=True)
                        self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["results"] = results
                        self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["status"] = "finished"
                    elif work.is_failed():
                        self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["status"] = "failed"

    def check_job_status(self, job) -> None:
        """
        Check the status of a job and update its state.

        Args:
            job: The job to check
        """
        if self.num_checks % 60 == 0:
            self.logger.info(f"Check job {job.job_id} status")

        # submit jobs which are not submitted
        if type(job) in [MultiStepsJob]:
            self.submit_job(job)

        if type(job) in [Job]:
            self.check_single_job_status(job)
        else:
            # if type(job) in [MulJob]:
            # submit jobs which are not submitted
            self.submit_multi_steps_job(job)

            self.check_multi_steps_job(job)

        self.num_checks += 1

    def cancel_job(self, job) -> None:
        """
        Cancel a job.

        Args:
            job: The job to cancel
        """
        for func_name in self.running_funcs[job.job_id]["funcs"]:
            for g_param_str in self.running_funcs[job.job_id]["funcs"][func_name]:
                work = self.running_funcs[job.job_id]["funcs"][func_name][g_param_str]["work"]
                if not work.is_terminated():
                    work.cancel()
