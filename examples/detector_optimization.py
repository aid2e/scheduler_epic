"""
Example usage of the Scheduler for ePIC EIC detector optimization.
"""

import numpy as np
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, JobLibRunner

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
    # Simulate detector performance
    # This is a simplified example - replace with actual simulation code
    
    # For this example, we'll use simplified formulas:
    # Better resolution (lower is better) with higher field and larger size
    resolution = 0.1 / field_strength * (1 + np.exp(-detector_length)) * (1 + np.exp(-detector_radius))
    
    # Better acceptance (higher is better) with larger detector
    acceptance = (1 - np.exp(-detector_length * detector_radius)) * 100
    
    # Higher cost with larger detector and stronger field
    cost = field_strength * 2 + detector_length * 10 + detector_radius * 15
    
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
    
    # Create a runner - use JobLib for local execution
    runner = JobLibRunner(n_jobs=-1)  # Use all available cores
    
    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    
    # Set the objective function
    scheduler.set_objective_function(optimization_function)
    
    # Run the optimization
    print("Starting optimization...")
    best_params = scheduler.run_optimization(max_trials=20)
    
    print("\nOptimization complete!")
    print("Best parameters:", best_params)
    
    # Evaluate the best configuration
    best_metrics = evaluate_detector_design(
        field_strength=best_params["field_strength"],
        detector_length=best_params["detector_length"],
        detector_radius=best_params["detector_radius"]
    )
    
    print("\nBest configuration performance:")
    for metric, value in best_metrics.items():
        print(f"{metric}: {value:.4f}")

if __name__ == "__main__":
    main()
