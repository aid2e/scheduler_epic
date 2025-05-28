"""
Example using container-based detector simulations with the Scheduler.
"""

import os
import json
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, SlurmRunner, JobType

def main():
    # Initialize Ax client
    ax_client = AxClient()
    
    # Define the parameter space for ePIC detector optimization
    ax_client.create_experiment(
        name="epic_detector_container_optimization",
        parameters=[
            {
                "name": "field_strength",
                "type": "range",
                "bounds": [1.0, 3.0],
                "value_type": "float",
            },
            {
                "name": "detector_length",
                "type": "range",
                "bounds": [3.0, 8.0],
                "value_type": "float",
            },
            {
                "name": "detector_radius",
                "type": "range",
                "bounds": [1.0, 2.5],
                "value_type": "float",
            },
            {
                "name": "detector_material", 
                "type": "choice", 
                "values": ["silicon", "germanium", "diamond"],
                "value_type": "str",
            },
            {
                "name": "n_events",
                "type": "fixed",
                "value": 10000,
                "value_type": "int",
            }
        ],
        objectives={
            "tracking_resolution": "minimize",
            "calorimeter_resolution": "minimize",
            "acceptance": "maximize",
            "cost": "minimize",
        },
    )
    
    # Create a Slurm runner configured for Singularity containers
    runner = SlurmRunner(
        partition="physics",
        time_limit="08:00:00",
        memory="16G",
        cpus_per_task=8,
        config={
            'modules': ['singularity', 'python/3.9'],
            'singularity_path': '/usr/bin/singularity',
            'sbatch_options': {
                'account': 'eic-project',
                'mail-user': 'your.email@example.com',
                'mail-type': 'END,FAIL'
            }
        }
    )
    
    # Create the scheduler
    scheduler = AxScheduler(
        ax_client, 
        runner,
        config={
            'monitoring_interval': 60,  # Check every minute
            'job_output_dir': '/scratch/eic/detector_sim_results',
            'max_trial_monitoring_time': 86400 * 7,  # 1 week maximum monitoring time
            'synchronous': False  # Run trials asynchronously
        }
    )
    
    # Set up container-based simulation
    # Assuming there's a container with ePIC detector simulation software
    scheduler.set_container_objective(
        container_image="eic/epic-sim:latest",
        container_command="python /app/run_simulation.py"
    )
    
    # Run batch of trials in parallel
    print("Starting batch optimization with containers...")
    
    with scheduler.batch_trial_context() as batch:
        # Add initial points to explore the parameter space
        batch.add_trial({
            "field_strength": 1.5,
            "detector_length": 4.0,
            "detector_radius": 1.5,
            "detector_material": "silicon",
            "n_events": 10000
        })
        
        batch.add_trial({
            "field_strength": 2.5,
            "detector_length": 6.0,
            "detector_radius": 2.0,
            "detector_material": "germanium",
            "n_events": 10000
        })
        
        batch.add_trial({
            "field_strength": 3.0,
            "detector_length": 8.0,
            "detector_radius": 2.5,
            "detector_material": "diamond",
            "n_events": 10000
        })
    
    # Now let Ax generate more trials based on the results
    for i in range(20):
        trial_index = scheduler.get_next_trial()
        if trial_index is None:
            break
            
        scheduler.run_trial(trial_index)
        
        # Continue immediately - trials will run asynchronously
        print(f"Started trial {trial_index}")
    
    # Monitor trials until they complete
    print("Monitoring trials...")
    while True:
        scheduler.monitor_trials()
        
        # Check if all trials are complete
        all_complete = True
        for trial_index, trial in scheduler.trials.items():
            print(f"Trial {trial_index}: {trial.state}")
            if trial.state not in [TrialState.COMPLETED, TrialState.FAILED, TrialState.CANCELLED]:
                all_complete = False
        
        if all_complete:
            break
            
        time.sleep(300)  # Check every 5 minutes
    
    # Get best parameters
    best_parameters, metrics = ax_client.get_best_parameters()
    
    print("\nOptimization complete!")
    print("Best parameters:", best_parameters)
    print("Best metrics:", metrics)
    
    # Save results
    scheduler.save_experiment("/scratch/eic/results/container_optimization_results.json")
    
    # Also save in a more readable format
    with open("/scratch/eic/results/best_detector_config.json", "w") as f:
        result = {
            "parameters": best_parameters,
            "metrics": metrics
        }
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
