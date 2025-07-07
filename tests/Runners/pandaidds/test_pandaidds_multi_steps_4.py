import logging
import json

from itertools import product
from ax.service.ax_client import AxClient, ObjectiveProperties
from scheduler import AxScheduler, PanDAiDDSRunner, JobLibRunner
from scheduler.utils.common import setup_logging
from scheduler.job.job import JobType
from scheduler.job.multi_steps_job import MultiStepsFunction


# define global parameters. It will generate a list of parameters working together with hyperparameters.
# For a group of hyperparameters, we may need to evaluate different types of events, then in the final
# step to merge the results.
# [{'eta_points': 0.1, 'particles': 'pi+'},
#  {'eta_points': 0.1, 'particles': 'kaon+'},
#  {'eta_points': 0.2, 'particles': 'pi+'},
#  {'eta_points': 0.2, 'particles': 'kaon+'}]
global_parameters = {
    "particles": ["pi+", "kaon+"],
    "eta_points": [0.1, 0.2]
}


# Define your objective function
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
    """
    Aggregates values from multiple JSON files.

    Each JSON file should contain a flat dictionary with numerical values.
    Repeated keys will have their values summed across files.

    Args:
        x, y: numeric values (e.g., coordinates or hyperparameters)
        particles: list or string of particles (unused here but likely part of parameter space)
        eta_points: list or float (same)
        input_file_names: list of file paths to load

    Returns:
        A dictionary with aggregated (summed) values by key.
    """
    print(f"input_file_names: {input_file_names}")
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


def objective_function_step_final(x, y, xyz):
    # print(f"global_parameters: {global_parameters}")
    sorted_keys = sorted(global_parameters.keys())
    combinations = [dict(zip(sorted_keys, values)) for values in product(*[global_parameters[k] for k in sorted_keys])]
    job_keys = combinations
    # print(f"job_keys: {job_keys}")
    # print(f"xyz: {xyz}")
    xyz_sum = sum([xyz[tuple(k.items())] for k in job_keys])
    return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2 + xyz_sum * 0.1}


# This file will be imported to load the objective function at remote sites in PanDA
# to avoid excuting the whole file, __name__ == "__main__" must be used.
# There is another way to only ship the codes of the objective function to remote sites.
# However, if this objective function calls some other functions, this way of only shipping
# the function codes will not work.
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

    logging.info("defining objectives")

    # PanDA attributes
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

    dataset_name_prefix = "user.wguan.my_experiment"

    # Create a runner
    runner = PanDAiDDSRunner(**panda_attrs)
    logging.info(f"created runner: {runner}")

    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    logging.info(f"created scheduler: {scheduler}")

    panda_idds_runner = PanDAiDDSRunner(**panda_attrs)

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
                # for 'input_file_names'. You can use any other names instead of 'input_file_name'.
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

    # Set the objective function
    scheduler.set_objective_function(objective_function)

    logging.info("running optimization")
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=10)
    print("Best parameters:", best_params)
