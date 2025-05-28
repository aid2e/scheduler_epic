"""
Example of using the Scheduler with Slurm for ePIC EIC detector optimization.
"""

import numpy as np
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, SlurmRunner

# Define your objective function for detector optimization
def evaluate_detector_design(field_strength, detector_length, detector_radius):
    """
    Example objective function for ePIC EIC detector optimization.
    
    Args:
        field_strength: Magnetic field strength in Tesla
        detector_length: Detector length in meters
        detector_radius: Detector radius in meters
        
    Returns:
        Dict with metrics: resolution, acceptance, cost
    """
    # This function would typically run a complex simulation
    # For this example, we'll use simplified formulas:
    
    # Better resolution (lower is better) with higher field and larger size
    resolution = 0.1 / field_strength * (1 + np.exp(-detector_length)) * (1 + np.exp(-detector_radius))
    
    # Better acceptance (higher is better) with larger detector
    acceptance = (1 - np.exp(-detector_length * detector_radius)) * 100
    
    # Higher cost with larger detector and stronger field
    cost = field_strength * 2 + detector_length * 10 + detector_radius * 15
    
    # Simulate a long-running computation
    import time
    time.sleep(10)  # This would be replaced with actual simulation code
    
    return {
        "resolution": resolution,  # Lower is better
        "acceptance": acceptance,  # Higher is better
        "cost": cost               # Lower is better
    }

# Wrapper function for Ax
def optimization_function(parameterization):
    """Wrapper for the objective function to use with Ax."""
    metrics = evaluate_detector_design(
        field_strength=parameterization["field_strength"],
        detector_length=parameterization["detector_length"],
        detector_radius=parameterization["detector_radius"]
    )
    return metrics

def main():
    # Initialize Ax client
    ax_client = AxClient()
    
    # Define the parameter space
    ax_client.create_experiment(
        name="epic_detector_optimization",
        parameters=[
            {
                "name": "field_strength",
                "type": "range",
                "bounds": [0.5, 3.0],
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
                "bounds": [0.8, 2.5],
                "value_type": "float",
            },
        ],
        objectives={
            "resolution": "minimize",
            "acceptance": "maximize",
            "cost": "minimize",
        },
    )
    
    # Create a Slurm runner
    runner = SlurmRunner(
        partition="physics",          # Slurm partition name
        time_limit="01:00:00",        # 1 hour time limit
        memory="8G",                  # 8GB memory per job
        cpus_per_task=4,              # 4 CPUs per job
        config={
            'sbatch_options': {
                'account': 'eic-project',  # Account to charge
                'mail-user': 'your.email@example.com',
                'mail-type': 'END,FAIL'
            }
        }
    )
    
    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    
    # Set the objective function
    scheduler.set_objective_function(optimization_function)
    
    # Run the optimization
    print("Starting optimization with Slurm...")
    best_params = scheduler.run_optimization(max_trials=20)
    
    print("\nOptimization complete!")
    print("Best parameters:", best_params)

if __name__ == "__main__":
    main()
