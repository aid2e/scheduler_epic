import logging

from ax.service.ax_client import AxClient, ObjectiveProperties
from scheduler import AxScheduler, PanDAiDDSRunner
from scheduler.utils.common import setup_logging


# Define your objective function
def objective_function(x, y):
    return {"objective": (x - 0.5) ** 2 + (y - 0.5) ** 2}

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

    # Create a runner
    runner = PanDAiDDSRunner(**panda_attrs)
    logging.info(f"created runner: {runner}")

    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    logging.info(f"created scheduler: {scheduler}")

    # Set the objective function
    scheduler.set_objective_function(objective_function)

    logging.info("running optimization")
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=10)
    print("Best parameters:", best_params)
