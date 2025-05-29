# Tutorial: Basic Detector Optimization

This tutorial shows how to use the Scheduler library for optimizing detector parameters. We'll create a simple objective function that evaluates detector performance based on field strength, detector length, and detector radius.

## Prerequisites

- Scheduler library installed (see [Installation](../installation.md))
- Basic understanding of Bayesian optimization with Ax
- `eic-shell` container and a own version of `epic` detector geometry 

## Step 1: Import Required Libraries

```python
import numpy as np
from ax.service.ax_client import AxClient
from scheduler import AxScheduler, JobLibRunner
```

## Step 2: Define Your Objective Function

Write the holistic example here

## Next Steps

- Try modifying the objective function to include more realistic detector physics
- Experiment with different parameter ranges and constraints
- Check out the [Slurm Execution Tutorial](slurm_execution.md) to scale up your optimization
