# Scheduler for Job Submission 
### (Under Development)

This repository is designed to create a scheduler that can submit jobs asynchronously using Joblib, Slurm, and Pandas.

## Dependencies

Please ensure all dependencies are satisfied before starting. A `requirements.txt` file will be provided later.

## Setup Instructions

To get started, follow the following steps:

1. Clone this repository:
    ```bash
    git clone <repository-url>
    ```

2. Run the setup script:
    ```bash
    ./setup.sh
    ```
    This script sets the necessary environment variables and checks for the `eic/epic` and `eic-shell` installations. If they are not present, the script will install them.

## Running the Scripts

To run the scripts in ePIC, follow these steps:

1. Start `eic-shell` (this needs to be done every time you start a new terminal session):
    ```bash
    ./eic-shell
    ```

2. Configure the build with CMake (run once):
    ```bash
    cd epic/
    cmake -B build -S . -DCMAKE_INSTALL_PREFIX=install
    ```

3. Build and install (run once):
    ```bash
    cmake --build build -- install -j7
    ```

4. Source the setup script (run every time you want to execute any ePIC scripts):
    ```bash
    source install/setup.sh
    ```

For more detailed instructions on running the scripts, follow the [ePIC tutorial](https://eic.github.io/documentation/tutorials.html).

