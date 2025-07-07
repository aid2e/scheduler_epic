#!/usr/bin/env python3
# Copyright (c) AID2E Team
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
from setuptools import setup, find_packages


def read_deps_from_file(filename):
    """Read in requirements file and return items as list of strings"""
    root_dir = os.path.dirname(__file__)
    filepath = os.path.join(root_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as fh:
            return [line.strip() for line in fh.readlines() 
                   if line.strip() and not line.startswith("#")]
    return []


# Core dependencies required for basic functionality
REQUIRES = [
    "ax-platform",  # For Ax integration
    "numpy",
    "pandas",
    "joblib",      # For JobLibRunner
    "scipy",
    "scikit-learn",
]

# Development dependencies
DEV_REQUIRES = [
    "pytest>=4.6",
    "pytest-cov",
    "black",
    "ruff",
    "isort",
    "mypy",
    "pre-commit",
    "types-setuptools",
]

# Read in pinned versions of the formatting tools
DEV_REQUIRES += read_deps_from_file("requirements-fmt.txt")

# Documentation dependencies
DOC_REQUIRES = [
    "mkdocs>=1.4.0",
    "mkdocs-material>=8.5.0",
    "pymdown-extensions>=9.0",
    "cairosvg>=2.5.0",
    "pillow>=9.0.0",
    "pygments>=2.14.0",
    "pydoc-markdown>=4.8.2",
    "sphinx",
    "sphinx-autodoc-typehints",
    "sphinx_rtd_theme",
]

# Testing dependencies (minimal set for basic unit tests)
UNITTEST_MINIMAL_REQUIRES = [
    "pytest>=4.6",
    "pytest-cov",
    "pytest-mock",
]

# Full testing dependencies
UNITTEST_REQUIRES = DEV_REQUIRES + UNITTEST_MINIMAL_REQUIRES + [
    "pytest-xdist",  # For parallel testing
    "coverage",
    "factory-boy",   # For test data generation
]

# Tutorial and example dependencies
TUTORIAL_REQUIRES = UNITTEST_REQUIRES + [
    "matplotlib",    # For plotting in tutorials
    "jupyter",       # For notebook tutorials
    "ipywidgets",    # For interactive widgets
    "plotly",        # For interactive plots
]

# Optional runtime dependencies
SLURM_REQUIRES = ["drmaa"]
PANDA_REQUIRES = ["panda-client"]
CONTAINER_REQUIRES = ["docker", "singularity-py"]


def local_version(version):
    """
    Patch in a version that can be uploaded to test PyPI
    """
    return ""


def setup_package() -> None:
    """Used for installing the scheduler package."""
    
    # Try to read README.md, fallback to a default description
    long_description = "A scheduler library for AID2E extending Ax functionality for ePIC EIC detector optimization"
    for readme_name in ["README.md", "readme.md", "README.rst", "readme.rst"]:
        try:
            with open(readme_name) as fh:
                long_description = fh.read()
            break
        except FileNotFoundError:
            continue

    setup(
        name="scheduler",
        version="0.1.0",
        description="A scheduler library for AID2E extending Ax functionality for ePIC EIC detector optimization",
        author="AID2E Team",
        author_email="ksuresh@wm.edu",
        license="MIT",
        url="https://github.com/aid2e/scheduler_epic",
        keywords=["Optimization", "Scheduling", "Detector", "Machine Learning"],
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Topic :: Scientific/Engineering",
            "Topic :: Scientific/Engineering :: Physics",
        ],
        long_description=long_description,
        long_description_content_type="text/markdown",
        python_requires=">=3.7",
        packages=find_packages(),
        install_requires=REQUIRES,
        extras_require={
            "dev": DEV_REQUIRES,
            "docs": DOC_REQUIRES,
            "unittest": UNITTEST_REQUIRES,
            "unittest_minimal": UNITTEST_MINIMAL_REQUIRES,
            "tutorial": TUTORIAL_REQUIRES,
            "slurm": SLURM_REQUIRES,
            "panda": PANDA_REQUIRES,
            "container": CONTAINER_REQUIRES,
            "all": (DEV_REQUIRES + DOC_REQUIRES + UNITTEST_REQUIRES + 
                   SLURM_REQUIRES + PANDA_REQUIRES + CONTAINER_REQUIRES),
        },
        package_data={
            # Include any data files in the package
            "scheduler": ["*.yaml", "*.yml", "*.json", "*.txt"],
        },
        entry_points={
            "console_scripts": [
                # Add command-line scripts here if needed
                # "scheduler-cli=scheduler.cli:main",
            ],
        },
    )


if __name__ == "__main__":
    setup_package()