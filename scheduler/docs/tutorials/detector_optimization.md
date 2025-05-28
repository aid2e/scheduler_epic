# Tutorial: Basic Detector Optimization

This tutorial shows how to use the Scheduler library for optimizing detector parameters. We'll create a simple objective function that evaluates detector performance based on field strength, detector length, and detector radius.

## Prerequisites

- Scheduler library installed (see [Installation](../installation.md))
- Basic understanding of Bayesian optimization with Ax

## Step 1: Import Required Libraries

```python
import numpy as np
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, JobLibRunner
```

## Step 2: Define Your Objective Function

Create a function that evaluates detector performance based on the input parameters:

```python
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
```

## Step 3: Create a Wrapper Function for Ax

Ax requires a specific function signature, so create a wrapper:

```python
def optimization_function(parameterization):
    """Wrapper for the objective function to use with Ax."""
    metrics = evaluate_detector_design(
        field_strength=parameterization["field_strength"],
        detector_length=parameterization["detector_length"],
        detector_radius=parameterization["detector_radius"]
    )
    return metrics
```

## Step 4: Initialize Ax Client and Define Parameter Space

```python
# Initialize Ax client
ax_client = AxClient()

# Define the parameter space
ax_client.create_experiment(
    name="epic_detector_optimization",
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
            "bounds": [4.0, 8.0],
            "value_type": "float",
        },
        {
            "name": "detector_radius",
            "type": "range",
            "bounds": [1.0, 3.0],
            "value_type": "float",
        },
    ],
    objectives={
        "resolution": "minimize",
        "acceptance": "maximize",
    },
    outcome_constraints=["cost <= 100.0"],
)
```

## Step 5: Create a Runner and Scheduler

```python
# Create a runner for local execution
runner = JobLibRunner(n_jobs=4)  # Use 4 cores

# Create the scheduler
scheduler = AxScheduler(ax_client, runner)

# Set the objective function
scheduler.set_objective_function(optimization_function)
```

## Step 6: Run the Optimization

```python
# Run the optimization
best_params = scheduler.run_optimization(max_trials=20)

# Print the results
print("Best parameters:")
print(best_params)

# Get the best metrics
best_metrics = ax_client.get_best_trial().values
print("Best metrics:")
print(best_metrics)
```

## Complete Example

Here's the complete example:

```python
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
                "bounds": [1.0, 3.0],
                "value_type": "float",
            },
            {
                "name": "detector_length",
                "type": "range",
                "bounds": [4.0, 8.0],
                "value_type": "float",
            },
            {
                "name": "detector_radius",
                "type": "range",
                "bounds": [1.0, 3.0],
                "value_type": "float",
            },
        ],
        objectives={
            "resolution": "minimize",
            "acceptance": "maximize",
        },
        outcome_constraints=["cost <= 100.0"],
    )
    
    # Create a runner for local execution
    runner = JobLibRunner(n_jobs=4)  # Use 4 cores
    
    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    
    # Set the objective function
    scheduler.set_objective_function(optimization_function)
    
    # Run the optimization
    best_params = scheduler.run_optimization(max_trials=20)
    
    # Print the results
    print("Best parameters:")
    print(best_params)
    
    # Get the best metrics
    best_metrics = ax_client.get_best_trial().values
    print("Best metrics:")
    print(best_metrics)

if __name__ == "__main__":
    main()
```

## Next Steps

- Try modifying the objective function to include more realistic detector physics
- Experiment with different parameter ranges and constraints
- Check out the [Slurm Execution Tutorial](slurm_execution.md) to scale up your optimization
