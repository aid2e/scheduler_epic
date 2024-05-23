from ax import RangeParameter, ParameterType, Objective, Experiment, SearchSpace, OptimizationConfig
from joblib_metric import ScriptExecutionMetric
from joblib_runner import JoblibJobRunner
import json
import argparse
import subprocess
from joblib_setup import run_dd_web_display, load_config, run_script
from ax.service.scheduler import Scheduler, SchedulerOptions
from ax.modelbridge.generation_strategy import GenerationStrategy
from ax.modelbridge.generation_strategy import GenerationStep
from ax.modelbridge.registry import Models
# from ax.metrics.noop import NoopMetric

## Setup the experiment
## ToDO: Define Search space , range of parameters and an analytic function


def make_experiment_with_runner_and_metric(script_path) -> Experiment:
    experiment = Experiment(
        name="script_execution_experiment",
        search_space=None,
        optimization_config=None,
        runner=JoblibJobRunner(),
        is_test=False,
    )
    # experiment.add_tracking_metric(NoopMetric(name="dummy_metric"))
    return experiment

def main():
    parser = argparse.ArgumentParser(description="Run scripts with joblib and handle outputs.")
    parser.add_argument('--config', type=str, help='Path to the configuration file.', default='config.json')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    script_path = config["scripts"]
    output_file = config["output_file"]

    # Run the script
    run_dd_web_display(script_path, output_file)
    
    # Create and run the experiment
    experiment = make_experiment_with_runner_and_metric(script_path)
    scheduler = Scheduler(
        experiment=experiment,
        generation_strategy=None,
        options=SchedulerOptions(),
    )
    scheduler.run_all_trials()

if __name__ == "__main__":
    main()


