#!/usr/bin/env python3


import random

# Generate two random numbers
num1 = random.randint(1, 100)
num2 = random.randint(1, 100)

# Add the two numbers
sum_of_numbers = num1 + num2

# Print the result
print(f"The sum of {num1} and {num2} is {sum_of_numbers}")


# import os
# import subprocess
# import json

# def load_config(config_path='config.json'):
#     """
#     Load configuration from a JSON file.
#     """
#     with open(config_path, 'r') as config_file:
#         return json.load(config_file)

# def source():
#     current_dir = os.path.dirname(os.path.realpath(__file__))
#     print(f"Current directory: {current_dir}")
#     epic_directory = os.path.join(current_dir, "epic")
#     print("epic_directory", epic_directory)
#     if os.path.exists(epic_directory):
#         setup_script = os.path.join(epic_directory, "install/setup.sh")
#         print("sourcing setup script: ", setup_script)
#         # Use a new shell instance to source the setup script
#         command = f"bash -c 'source {setup_script} && env'"
#         proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, executable='/bin/bash')
#         for line in proc.stdout:
#             key, _, value = line.decode().partition("=")
#             os.environ[key] = value.strip()

# def run_dd_web_display(script_path, output_file):
#     """
#     Runs the dd_web_display command with the provided script and output file.
#     """
#     command = f"dd_web_display -o {output_file} --export {script_path} -k"
#     print("Running command:", command)
#     subprocess.run(command, shell=True, check=True)



# if __name__ == "__main__":

#     config = load_config()
#     # Define the paths for the script and output file
#     script_path = config['scripts']
#     output_file = config['output_file']
    
#     source()
#     # Run the dd_web_display command
#     run_dd_web_display(script_path, output_file)
#     print(f"dd_web_display completed successfully. Output saved to {output_file}.")
