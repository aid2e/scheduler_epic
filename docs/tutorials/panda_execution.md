# Tutorial: Using PanDA Execution

The PanDA (Production and Distributed Analysis) system is a high-performance workload management system originally developed by the ATLAS experiment at CERN. It is now widely used for managing distributed computing workloads across Grid, Cloud, and HPC environments. The iDDS (intelligent Data Delivery Service) is a powerful and flexible workflow system to orchestrate multi-step, data-aware, and ML-friendly workflows over distributed computing systems.

This tutorial explains how to use PANDA execution with the Scheduler for AID2E.

## Prerequisites
- User registeration based on CILogon https://panda-iam-doma.cern.ch/
- PanDA documents https://panda-wms.readthedocs.io/en/latest/
- iDDS documents https://idds.readthedocs.io/en/latest/

## Initialize the environment

```python
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip black ruff
pip install idds-client idds-common idds-workflow panda-client
```

## Setup the environment

- Setup virturl environment

```python
source ./setup.sh
```

setup.sh [`https://github.com/aid2e/scheduler_epic/blob/pandaidds/setup.sh`]

- Setup PanDA(BNL) environment (This PanDA service is maintained by BNL to run jobs at WLCG, OSG, HPC and so on, with Rucio integrated).
```python
source setup_panda_bnl.sh
```
`setup_panda_bnl.sh` [`https://github.com/aid2e/scheduler_epic/blob/pandaidds/setup_panda_bnl.sh`]

## Simple example

# Setup 1: import python libraries
```python
import logging

from ax.service.ax_client import AxClient, ObjectiveProperties
from scheduler import AxScheduler, PanDAiDDSRunner
from scheduler.utils.common import setup_logging
```

# Setup 2: Define the objectvie function
```python
def objective_function(x, y):
    return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2}
```

# Setup 3: Initialize the Ax client and create the experiment

With python libraries like `cloudpickle` and `dill`, users can ship the function codes to remote computing resources
to execute them. However, in complex use cases, one function may need to call a lot of other functions and libraries
developed. Many of them are locally developed. Instead of only shipping the codes of one function to remote computing
resources. The idea of PanDA-iDDS is to ship all codes in the current working directory and then try to import them at
remote computing resources.

NOTE: The python codes will be imported at remote computing resources. To avoid executing some codes during importing,
You need to put those codes in `if __name__ == "__main__":`

```python
if __name__ == "__main__":
    setup_logging(log_level="debug")

    logging.debug("setup ax client")
    # Initialize Ax client
    ax_client = AxClient()

    logging.info("Creating experiment")

    # Define your parameter space
    ax_client.create_experiment(
        name="my_experiment",
        parameters=[
            {
                "name": "x",
                "type": "range",
                "bounds": [0.0, 1.0],
                "value_type": "float",
            },
            {
                "name": "y",
                "type": "range",
                "bounds": [0.0, 1.0],
                "value_type": "float",
            },
        ],
        objectives={"objective": ObjectiveProperties(minimize=True)},
    )
```

# Step 4: Initializa the PanDA runner

```
    # Virtual env deployed on cvmfs
    # Libaries like Ax are required during importing at remote computing resources.
    init_env = [
        "source /cvmfs/unpacked.cern.ch/registry.hub.docker.com/fyingtsai/eic_xl:24.11.1/opt/conda/setup_mamba.sh;"
        "source /cvmfs/unpacked.cern.ch/registry.hub.docker.com/fyingtsai/eic_xl:24.11.1/opt/conda/dRICH-MOBO//MOBO-tools/setup_new.sh;"
        "command -v singularity &> /dev/null || export SINGULARITY=/cvmfs/oasis.opensciencegrid.org/mis/singularity/current/bin/singularity;"
        "export AIDE_HOME=$(pwd);"
        "export PWD_PATH=$(pwd);"
        'export SINGULARITY_OPTIONS="--bind /cvmfs:/cvmfs,$(pwd):$(pwd)"; '
        "export SIF=/cvmfs/singularity.opensciencegrid.org/eicweb/eic_xl:24.11.1-stable; export SINGULARITY_BINDPATH=/cvmfs,/afs; "
        "env; "
    ]
    init_env = " ".join(init_env)

    panda_attrs = {
        "name": "user.wguan.my_experiment",
        "init_env": init_env,
        "cloud": "US",
        "queue": "BNL_PanDA_1",  # BNL_OSG_PanDA_1, BNL_PanDA_1
        "source_dir": None,  # used to upload files in the source directory to PanDA, which will be used for the remote jobs.
                             # None is the current directory.
        "source_dir_parent_level": 1,
        "exclude_source_files": [
            r"(^|/)\.[^/]+",    # file starts with "."
            "doc*", "DTLZ2*", ".*json", ".*log", "work", "log", "OUTDIR",
            "calibrations", "fieldmaps", "gdml", "EICrecon-drich-mobo",
            "eic-software", "epic-geom-drich-mobo", "irt", "share", "back*",
            "__pycache__"
        ],
        "max_walltime": 3600,
        "core_count": 1,
        "total_memory": 4000,
        "enable_separate_log": True,
        "job_dir": None,
    }

    # Create a runner
    runner = PanDAiDDSRunner(**panda_attrs)
    logging.info(f"created runner: {runner}")
```

# Step 5: Create a scheduler to run optimization

```python
    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    logging.info(f"created scheduler: {scheduler}")

    # Set the objective function
    scheduler.set_objective_function(objective_function)

    logging.info("running optimization")
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=10)
    print("Best parameters:", best_params)
```

# Step 6: Complete Example

The full example can be found in `test_pandaidds_simple.py` [`https://github.com/aid2e/scheduler_epic/blob/pandaidds/tests/pandaidds/test_pandaidds_simple.py`]

## Multiple Step example
This example is similar to the example above. Here we only show the differences.

# Define multiple step functions

In this example, `x` and `y` and hyperparameters which will be filled by Ax. `xyz` is the results from the first function. The system will automatically
collect the results from the first function and fill it to the second function for every set of hyperparameter `x` and `y`.

```python
# Define your objective function
def objective_function_step(x, y):
    return {"xyz": (x - 0.5) ** 2 + (y - 0.5) ** 2}


def objective_function_ana(x, y, xyz):
    return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2 + xyz * 0.1}
```

# Define the objective function with a MultiStepFunction
In the MultiStepFunction, the first step runs with PanDAiDDSRunner and the second step runs at local JobLibRunner.

```python
    objective_function = MultiStepsFunction(
        objective_funcs={
            "simrecoana": {
                "func": objective_function_step,
                "job_type": JobType.FUNCTION,
                "runner": PanDAiDDSRunner(**panda_attrs)
            },
            "final": {
                "func": objective_function_ana,
                "job_type": JobType.FUNCTION,
                "runner": JobLibRunner(n_jobs=-1),
                "parent_result_parameter_name": "xyz",
            },
        },
        deps={
            "final": {"parent": "simrecoana", "dep_type": "results", "dep_map": "one2one"},
        },
        final="final",    # if final is not set, it will use the last step in objective_funcs.
                          # The final step will set its result as the job's result
    )
```

# Full MultiStepFunction example
The full example can be found in `test_pandaidds_multi_steps_2.py` [`https://github.com/aid2e/scheduler_epic/blob/pandaidds/tests/pandaidds/test_pandaidds_multi_steps_2.py`]

## Multiple Step with global parameters

For a set of hyperparameters, one may need to evaluate it with different conditions. For example, for detector design,
with on detecotr setting, we may need to evaluate the detector performance against different types of particles. Global
parameters are designed for it.

# Global parameters
```python
global_parameters = {
    "particles": ["pi+", "kaon+"],
    "eta_points": [0.1, 0.2]
}
```
In this example, it will generate a lit of parameters. For every set of hyperparameters, it will execute the objective
function 4 times with one column in the list of the parameters below.
```python
 [{'eta_points': 0.1, 'particles': 'pi+'},
  {'eta_points': 0.1, 'particles': 'kaon+'},
  {'eta_points': 0.2, 'particles': 'pi+'},
  {'eta_points': 0.2, 'particles': 'kaon+'}]
```

# Define objective function

In the objective function, `x` and `y` are hyperparameters. `particles` and `eta_points` are global parameters.

```python
def objective_function_step(x, y, particles, eta_points):
    if particles == "pi+":
        return {"xyz": ((x - 0.5) ** 3 + (y - 0.5) ** 3) * eta_points}
    elif particles == "kaon+":
        return {"xyz": ((x - 0.5) ** 2 + (y - 0.5) ** 2) * eta_points}
    else:
        return {"xyz": 0.1}
```

# Merge objectives

In this example, the fist step will return `xyz`. However, with different global parameters, it will return a different result.
If we define the dependency map previous step and the merge step is `all2one`. The return value {`xzz`: <value>} will be mapped
to:
```python
{
    `xyz`: {
        (('eta_points': 0.1), ('particles': 'pi+')): <value1>,
        (('eta_points': 0.1), ('particles': 'kaon+')): <value2>,
        (('eta_points': 0.2), ('particles': 'pi+')): <value3>,
        (('eta_points': 0.2), ('particles': 'kaon+')): <value4>
    }
}
```

Here is an example of the merge function.
```
def objective_function_ana(x, y, xyz):
    # print(f"global_parameters: {global_parameters}")
    sorted_keys = sorted(global_parameters.keys())
    combinations = [dict(zip(sorted_keys, values)) for values in product(*[global_parameters[k] for k in sorted_keys])]
    job_keys = combinations
    # print(f"job_keys: {job_keys}")
    # print(f"xyz: {xyz}")
    xyz_sum = sum([xyz[tuple(k.items())] for k in job_keys])
    return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2 + xyz_sum * 0.1}
```

# Define the objective function of MultiStepFunction with global parameters
```python
    objective_function = MultiStepsFunction(
        objective_funcs={
            "simrecoana": {
                "func": objective_function_step,
                "job_type": JobType.FUNCTION,
                "runner": PanDAiDDSRunner(**panda_attrs)
            },
            "final": {
                "func": objective_function_ana,
                "job_type": JobType.FUNCTION,
                "runner": JobLibRunner(n_jobs=-1),
                "parent_result_parameter_name": "xyz",
            },
        },
        deps={
            "final": {"parent": "simrecoana", "dep_type": "results", "dep_map": "all2one"},
        },
        global_parameters=global_parameters,
        global_parameters_steps=["simrecoana"],
        final="final",                # if final is not set, it will use the last step in objective_funcs.
                                      # The final step will set its result as the job's result
    )
```

# Full MultiStepFunction example
The full example can be found in `test_pandaidds_multi_steps_3.py` [`https://github.com/aid2e/scheduler_epic/blob/pandaidds/tests/pandaidds/test_pandaidds_multi_steps_3.py`]


## Multiple Step with Rucio supports

Rucio is a large-scale, distributed data management system. Here we will use Rucio to manage input/output datasets.

# Define the objective functions

In the `objective_function_step_simreco` function, we write the results to a file. We will upload this file to Rucio.
(In real use cases, this step should generate root files which are big and the content of the root files are difficult
to be transferred through function return values. So we need to store the root files in some storages with Rucio.)

In the `objective_function_step_ana` function, we have a new parameter `input_file_names` as a placeholder for the list
of file names from a dataset (we will describe how to tell PanDA to fill this parameter later).

```python
def objective_function_step_simreco(x, y, particles, eta_points):
    if particles == "pi+":
        ret = {"xyz": ((x - 0.5) ** 3 + (y - 0.5) ** 3) * eta_points}
    elif particles == "kaon+":
        ret = {"xyz": ((x - 0.5) ** 2 + (y - 0.5) ** 2) * eta_points}
    else:
        ret = {"xyz": 0.1}

    with open("my_test.txt", "w") as f:
        json.dump(ret, f)


def objective_function_step_ana(x, y, particles, eta_points, input_file_names):
    ret = {}

    for input_file_name in input_file_names:
        try:
            with open(input_file_name, "r") as f:
                data = json.load(f)
                for k, v in data.items():
                    # Assumes v is numeric; otherwise raises an error
                    ret[k] = ret.get(k, 0) + v
        except Exception as e:
            print(f"Error reading file {input_file_name}: {e}")

    return ret
```

# Define the objective function of MultiStepFunction with datasets

In this example, for the `simreco` step, we set `with_output_dataset` and define the `output_file` and `output_dataset`.
The output file must be produced by `objective_function_step_simreco`. Otherwise PanDA will report errors that
`output_file` cannot be found. Here we defined total events `num_events`=200 and `num_events_per_job`=100. So PanDA will
generate two jobs. Every job will produce one `output_file` with name `my_test.txt`. To avoid overwriting each other,
before uploading the `output_file` to Rucio, PanDA will rename the output with
`dataset_name`+`additional sequence name`+`output_file name`.

In the `ana` (analysis) step, we set `with_input_datasets` and define
`"input_datasets": {"input_file_names": f"{dataset_name_prefix}.simreco.#global_parameter_key.#job_id"}`. Here the dataset
name should be the same dataset name of the previous step. PanDA-iDDS will get the list of files in the input dataset and
create an additional argument `"input_file_names=<file_list_in_dataset>"`. So the function `objective_function_step_ana`
must have a placeholder argument for `'input_file_names'`. You can use any other names instead of `'input_file_names'`.

In this example, we set `dep_type` to `datasets` and `return_func_results` to False. The scheduler will not wait for
function results. PanDA will automatically trigger the next step when the datasets in `simreco` are done.

```python
    objective_function = MultiStepsFunction(
        objective_funcs={
            "simreco": {
                "func": objective_function_step_simreco,
                "job_type": JobType.FUNCTION,
                "runner": panda_idds_runner,
                "return_func_results": False,    # here the outputs are in dataset, so no need to wait for function outputs
                "with_output_dataset": True,
                "output_file": "my_test.txt",
                # if global parameters are used, please add '#global_parameter_key' to
                # the dataset name. PanDA-iDDS will automatically replace it to different
                # keys based on the global parameters. Otherwise, all files with different
                # global parameters will be in the same dataset.
                "output_dataset": f"{dataset_name_prefix}.simreco.#global_parameter_key.#job_id",
                "num_events": 200,
                "num_events_per_job": 100,
            },
            "ana": {
                "func": objective_function_step_ana,
                "job_type": JobType.FUNCTION,
                "runner": panda_idds_runner,
                "with_input_datasets": True,
                # Here the dataset name should be the same dataset name of the previous step.
                # PanDA-iDDS will get the list of files in the input dataset and create an
                # additional argument "input_file_names=<file_list_in_dataset>".
                # So the function objective_function_step_ana must have a placeholder argument
                # for 'input_file_names'. You can use any other names instead of 'input_file_names'.
                "input_datasets": {"input_file_names": f"{dataset_name_prefix}.simreco.#global_parameter_key.#job_id"},
            },
            "final": {
                "func": objective_function_step_final,
                "job_type": JobType.FUNCTION,
                "runner": JobLibRunner(n_jobs=-1),
                "parent_result_parameter_name": "xyz",      # will add a parameter xyz=<get_parent_results> to the func
            },
        },
        deps={
            "final": {"parent": "ana", "dep_type": "results", "dep_map": "all2one"},
            "ana": {"parent": "simreco", "dep_type": "datasets", "dep_map": "one2one"},    # depends on the dataset. It will use rucio to manage the datasets.
        },
        global_parameters=global_parameters,
        global_parameters_steps=["simreco", "ana"],
        final="final",    # if final is not set, it will use the last step in objective_funcs.
                          # The final step will set its result as the job's result
    )
```

# Full MultiStepFunction with Rucio example
The full example can be found in `test_pandaidds_multi_steps_4.py` [`https://github.com/aid2e/scheduler_epic/blob/pandaidds/tests/pandaidds/test_pandaidds_multi_steps_4.py`] and
`test_pandaidds_multi_steps_5.py` [`https://github.com/aid2e/scheduler_epic/blob/pandaidds/tests/pandaidds/test_pandaidds_multi_steps_5.py`]. The difference between `test_pandaidds_multi_steps_4.py` and `test_pandaidds_multi_steps_5.py` is the `return_func_results`.
