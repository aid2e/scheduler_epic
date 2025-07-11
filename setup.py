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
    author="Your Name",
    author_email="your.email@example.com",
    description="A scheduler library for AID2E extending Ax functionality for ePIC EIC detector optimization",
    long_description=open("readme.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/scheduler",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
