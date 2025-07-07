from setuptools import setup, find_packages

setup(
    name="scheduler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ax-platform",  # For Ax integration
        "numpy",
        "pandas",
        "joblib",      # For JobLibRunner
    ],
    extras_require={
        "slurm": ["drmaa"],  # Optional dependency for Slurm support
        "panda": ["panda-client"],  # Optional dependency for PanDA support
    },
    author="AID2E Team",
    author_email="ksuresh@wm.edu",
    description="A scheduler library for AID2E extending Ax functionality for ePIC EIC detector optimization",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aid2e/scheduler_epic",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)