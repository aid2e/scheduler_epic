# Scheduler for AID2E Documentation

Welcome to the documentation for the Scheduler library, a Python package for scheduling and managing optimization trials for the ePIC EIC detector design using Ax.

## Overview

The Scheduler library extends the Ax platform for Bayesian optimization with additional features for managing and executing trials on various compute backends. It's designed to facilitate parameter optimization for detector simulations and other computationally intensive tasks.

## Key Features

- **Ax Integration**: Seamlessly works with the Ax platform for Bayesian optimization
- **Multiple Job Types**:
  - Python functions
  - Shell/Python scripts
  - Containers (Docker/Singularity)
- **Multiple Execution Backends**:
  - JobLib for local parallel execution
  - Slurm for cluster computing
  - PanDA for distributed computing
- **Trial Management**: Comprehensive trial state tracking and monitoring
- **Flexible Execution**: Support for synchronous or asynchronous execution modes
- **Batch Processing**: Submit multiple trials in parallel for efficient exploration
- **Persistence**: Save and load experiments to resume optimization

## Getting Started

- [Installation](installation.md): How to install the Scheduler library
- [Quick Start](quickstart.md): Get up and running with simple examples
- [Tutorials](tutorials/index.md): Step-by-step guides for common use cases
- [API Reference](api/index.md): Detailed documentation of classes and methods

## Architecture

See the [Architecture Overview](architecture.md) for a high-level understanding of how the components interact.
