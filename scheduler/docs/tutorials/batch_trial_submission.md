# Tutorial: Batch Trial Submission

This tutorial demonstrates how to use the batch trial submission feature of the Scheduler library. Batch trials allow you to submit multiple trials at once, which can be more efficient than submitting them one by one.

## Prerequisites

- Scheduler library installed
- Basic understanding of the Scheduler and Ax

## Step 1: Import Required Libraries

```python
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, JobLibRunner
```

## Step 2: Define Your Objective Function

```python
def objective_function(parameterization):
    """Simple objective function for demonstration."""
    x = parameterization["x"]
    y = parameterization["y"]
    
    # Simple objective function: Rosenbrock function
    a = 1
    b = 100
    objective = (a - x)**2 + b * (y - x**2)**2
    
    return {"objective": objective}
```

## Step 3: Initialize Ax Client and Define Parameter Space

```python
# Initialize Ax client
ax_client = AxClient()

# Define the parameter space
ax_client.create_experiment(
    name="batch_trial_demo",
    parameters=[
        {
            "name": "x",
            "type": "range",
            "bounds": [-2.0, 2.0],
            "value_type": "float",
        },
        {
            "name": "y",
            "type": "range",
            "bounds": [-2.0, 2.0],
            "value_type": "float",
        },
    ],
    objectives={"objective": "minimize"},
)
```

## Step 4: Create a Runner and Scheduler

```python
# Create a runner for local execution
runner = JobLibRunner(n_jobs=4)  # Use 4 cores

# Create the scheduler
scheduler = AxScheduler(ax_client, runner)

# Set the objective function
scheduler.set_objective_function(objective_function)
```

## Step 5: Use Batch Trial Context

```python
# Create a batch of trials
with scheduler.batch_trial_context() as batch:
    # Add trials with specific parameter values
    batch.add_trial({"x": 0.5, "y": 0.5})
    batch.add_trial({"x": -0.5, "y": 0.5})
    batch.add_trial({"x": 0.5, "y": -0.5})
    batch.add_trial({"x": -0.5, "y": -0.5})
    
    # The trials will be run when exiting the context
```

## Step 6: Run Additional Optimization

```python
# Run more trials using standard optimization
best_params = scheduler.run_optimization(max_trials=10)

# Print the results
print("Best parameters:")
print(best_params)
```

## Complete Example

Here's the complete example:

```python
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, JobLibRunner

def objective_function(parameterization):
    """Simple objective function for demonstration."""
    x = parameterization["x"]
    y = parameterization["y"]
    
    # Simple objective function: Rosenbrock function
    a = 1
    b = 100
    objective = (a - x)**2 + b * (y - x**2)**2
    
    return {"objective": objective}

def main():
    # Initialize Ax client
    ax_client = AxClient()
    
    # Define the parameter space
    ax_client.create_experiment(
        name="batch_trial_demo",
        parameters=[
            {
                "name": "x",
                "type": "range",
                "bounds": [-2.0, 2.0],
                "value_type": "float",
            },
            {
                "name": "y",
                "type": "range",
                "bounds": [-2.0, 2.0],
                "value_type": "float",
            },
        ],
        objectives={"objective": "minimize"},
    )
    
    # Create a runner for local execution
    runner = JobLibRunner(n_jobs=4)  # Use 4 cores
    
    # Create the scheduler
    scheduler = AxScheduler(ax_client, runner)
    
    # Set the objective function
    scheduler.set_objective_function(objective_function)
    
    # Create a batch of trials with manually specified values
    print("Running batch of manually specified trials...")
    with scheduler.batch_trial_context() as batch:
        # Add trials with specific parameter values
        batch.add_trial({"x": 0.5, "y": 0.5})
        batch.add_trial({"x": -0.5, "y": 0.5})
        batch.add_trial({"x": 0.5, "y": -0.5})
        batch.add_trial({"x": -0.5, "y": -0.5})
    
    # Print results of the batch trials
    print("\nResults from batch trials:")
    for trial_idx in range(ax_client.experiment.num_trials):
        trial = ax_client.experiment.trials[trial_idx]
        params = trial.arm.parameters
        metrics = trial.objective_mean
        print(f"Trial {trial_idx}: Params {params}, Objective: {metrics}")
    
    # Run more trials using standard optimization
    print("\nRunning additional optimization trials...")
    best_params = scheduler.run_optimization(max_trials=6)  # 6 more trials
    
    # Print the final results
    print("\nBest parameters after all trials:")
    print(best_params)
    
    # Save the experiment for later analysis
    scheduler.save_experiment("batch_trial_results.json")

if __name__ == "__main__":
    main()
```

## Advanced: Batch Trials with Ax Generation Strategy

You can also combine batch trials with Ax's generation strategy to generate multiple parameter sets at once:

```python
# Create a batch of model-generated trials
print("Running batch of model-generated trials...")
with scheduler.batch_trial_context() as batch:
    # Generate multiple parameter sets using the model
    for _ in range(4):
        parameters, trial_index = ax_client.get_next_trial()
        # Add the trial to the batch
        batch.add_trial(parameters)
```

## Advanced: Asynchronous Batch Execution

For more efficient resource utilization, you can run batch trials asynchronously:

```python
# Create the scheduler with asynchronous execution
scheduler = AxScheduler(
    ax_client, 
    runner,
    config={
        'synchronous': False,  # Run trials asynchronously
        'monitoring_interval': 1  # Check status every second
    }
)

# Set the objective function
scheduler.set_objective_function(objective_function)

# Create an asynchronous batch of trials
with scheduler.batch_trial_context() as batch:
    for _ in range(10):
        parameters, trial_index = ax_client.get_next_trial()
        batch.add_trial(parameters)

# Wait for all trials to complete
scheduler.wait_for_completed_trials()
```

## Next Steps

- Combine batch trials with [Slurm Execution](slurm_execution.md) for high-performance computing
- Use batch trials with [Container-Based Optimization](container_based_optimization.md) for reproducible experiments
- Learn about saving and loading experiments in the [Experiment Persistence](experiment_persistence.md) tutorial
