# Installation

This guide covers how to install the Scheduler library for AID2E.

## Prerequisites

- Python 3.7 or later
- pip package manager

## Basic Installation

You can install the Scheduler library from source:

```bash
# Clone the repository
git clone https://github.com/yourusername/scheduler.git
cd scheduler

# Install the basic package
pip install -e .
```

## Installation with Specific Backends

The Scheduler supports different execution backends. You can install the dependencies for the ones you need:

### With Slurm Support

```bash
pip install -e .[slurm]
```

### With PanDA Support

```bash
pip install -e .[panda]
```

### With All Features

```bash
pip install -e .[slurm,panda]
```

## Development Installation

For development purposes, you may want to install the development dependencies:

```bash
pip install -e .[dev]
```

or

```bash
pip install -r requirements-dev.txt
```

## Verifying Installation

You can verify that the installation was successful by running:

```python
import scheduler
print(scheduler.__version__)
```

This should print the version number of the installed package.

## System Requirements

- **Local Execution (JobLibRunner)**: Any system with Python and sufficient RAM/CPU for your tasks
- **Slurm Execution (SlurmRunner)**: Access to a Slurm cluster
- **PanDA Execution (PanDARunner)**: Access to the PanDA distributed computing system
