"""
SlurmRunner - Runner that submits jobs to SLURM based on job type.
"""

import os
import uuid
import json
import datetime
import logging
import subprocess
import pickle
import sys
import shlex
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

from ..job.job import JobType
from ..job.job_state import JobState
from .base_runner import BaseRunner


class SlurmRunner(BaseRunner):
    """
    A runner that submits different types of jobs to SLURM.
    Supports FUNCTION, SCRIPT, and CONTAINER job types.
    """

    def __init__(
        self,
        name: str = None,
        partition: str = "batch",
        time_limit: str = "01:00:00",
        memory: str = "4G",
        cpus_per_task: int = 1,
        nodes: int = 1,
        ntasks_per_node: int = 1,
        account: Optional[str] = None,
        qos: Optional[str] = None,
        config: Dict[str, Any] = None,
    ):
        """Initialize a new SlurmRunner."""
        super().__init__(config or {})
        
        self.name = name or "slurm_runner"
        self.partition = partition
        self.time_limit = time_limit
        self.memory = memory
        self.cpus_per_task = cpus_per_task
        self.nodes = nodes
        self.ntasks_per_node = ntasks_per_node
        self.account = account
        self.qos = qos

        # Get configuration options
        self.modules = self.config.get("modules", [])
        self.python_path = self.config.get("python_path", "python")
        self.conda_env = self.config.get("conda_env", None)
        self.init_env = self.config.get("init_env", [])  # Additional environment setup

        # Directory to store job files
        self.job_dir = self.config.get("job_dir", os.path.expanduser("~/slurm_jobs"))
        self.job_dir = Path(self.job_dir)
        self.job_dir.mkdir(parents=True, exist_ok=True)

        # Track submitted jobs
        self.jobs = {}
        self.running_funcs = {}
        self.workflow = None
        self.workflow_id = None
        
        self.logger = logging.getLogger("SlurmRunner")
        self.num_checks = 0

    def submit_workflow(self, job) -> object:
        """Initialize workflow if not already done."""
        if not self.workflow:
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.workflow_id = f"slurm_wf_{now}_{uuid.uuid4().hex[:6]}"
            self.workflow = {"id": self.workflow_id}
            self.logger.info(f"Initialized SLURM workflow {self.workflow_id}")
        return self.workflow

    def _create_function_execution_script(self, job_dir: Path) -> str:
        """Create script for executing a serialized Python function."""
        script_content = '''#!/usr/bin/env python3
"""
SLURM job execution script - loads and executes the serialized function.
"""

import pickle
import json
import sys
import traceback
from pathlib import Path

def main():
    """Main execution function."""
    try:
        # Load the serialized function
        with open('function.pkl', 'rb') as f:
            func = pickle.load(f)
        
        # Load the parameters
        with open('params.pkl', 'rb') as f:
            params = pickle.load(f)
        
        print(f"Executing function: {getattr(func, '__name__', 'unknown')}")
        print(f"Parameters: {params}")
        
        # Execute the function with the parameters
        result = func(**params)
        
        print(f"Function completed successfully")
        print(f"Result: {result}")
        
        # Save the result as JSON
        with open('result.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print("Result saved to result.json")
        
    except Exception as e:
        error_info = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "function_name": getattr(func, '__name__', 'unknown') if 'func' in locals() else 'unknown'
        }
        
        print(f"Function execution failed: {e}")
        print("Full traceback:")
        print(traceback.format_exc())
        
        # Save error information
        with open('error.json', 'w') as f:
            json.dump(error_info, f, indent=2)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        return script_content

    def _substitute_parameters(self, text: str, params: Dict[str, Any]) -> str:
        """Substitute parameters in text using {param_name} format."""
        try:
            return text.format(**params)
        except KeyError as e:
            self.logger.warning(f"Parameter {e} not found for substitution in: {text}")
            return text

    def _create_slurm_script(self, job, job_dir: Path) -> str:
        """Create a SLURM batch script based on job type."""
        slurm_script = "#!/bin/bash\n"
        
        # SLURM directives
        slurm_script += f"#SBATCH --job-name={job.job_id}\n"
        slurm_script += f"#SBATCH --partition={self.partition}\n"
        slurm_script += f"#SBATCH --time={self.time_limit}\n"
        slurm_script += f"#SBATCH --mem-per-cpu={self.memory}\n"
        slurm_script += f"#SBATCH --cpus-per-task={self.cpus_per_task}\n"
        slurm_script += f"#SBATCH --nodes={self.nodes}\n"
        slurm_script += f"#SBATCH --ntasks-per-node={self.ntasks_per_node}\n"
        slurm_script += f"#SBATCH --output={job_dir}/slurm_%j.out\n"
        slurm_script += f"#SBATCH --error={job_dir}/slurm_%j.err\n"
        
        if self.account:
            slurm_script += f"#SBATCH --account={self.account}\n"
        if self.qos:
            slurm_script += f"#SBATCH --qos={self.qos}\n"
        
        slurm_script += "\n"
        
        # Environment setup
        slurm_script += "# Environment setup\n"
        slurm_script += "set -e  # Exit on error\n"
        slurm_script += f"cd {job_dir}\n"
        slurm_script += "\n"
        
        # Load modules if specified
        if self.modules:
            slurm_script += "# Load environment modules\n"
            for module in self.modules:
                slurm_script += f"module load {module}\n"
            slurm_script += "\n"
        
        # Additional environment initialization
        if self.init_env:
            slurm_script += "# Additional environment setup\n"
            for env_cmd in self.init_env:
                env_cmd = self._substitute_parameters(env_cmd, job.params)
                slurm_script += f"{env_cmd}\n"
            slurm_script += "\n"
        
        # Activate conda environment if specified
        if self.conda_env:
            slurm_script += f"# Activate conda environment\n"
            slurm_script += f"conda activate {self.conda_env}\n"
            slurm_script += "\n"
        
        # Job-specific execution based on job type
        if job.job_type == JobType.FUNCTION:
            slurm_script += "# Execute Python function\n"
            slurm_script += "echo 'Starting function execution...'\n"
            slurm_script += f"{self.python_path} execute_function.py\n"
            slurm_script += "echo 'Function execution completed.'\n"
            
        elif job.job_type == JobType.SCRIPT:
            slurm_script += "# Execute script\n"
            slurm_script += "echo 'Starting script execution...'\n"
            
            # Handle script execution with parameter substitution
            script_path = job.script_path
            if script_path:
                # If script path is provided, execute it with parameters as command line args
                script_path = self._substitute_parameters(script_path, job.params)
                slurm_script += f"{script_path}"
                
                # Add parameters as command line arguments
                for key, value in job.params.items():
                    slurm_script += f" {key} {value}"
                slurm_script += "\n"
            else:
                # If no script path, assume we have commands in job config
                commands = job.params.get('commands', [])
                if isinstance(commands, str):
                    commands = [commands]
                
                for command in commands:
                    command = self._substitute_parameters(command, job.params)
                    slurm_script += f"{command}\n"
            
            slurm_script += "echo 'Script execution completed.'\n"
            
        elif job.job_type == JobType.CONTAINER:
            slurm_script += "# Execute container\n"
            slurm_script += "echo 'Starting container execution...'\n"
            
            container_image = job.container_image
            container_command = job.container_command or ""
            container_command = self._substitute_parameters(container_command, job.params)
            
            # Example singularity execution - adjust based on your cluster
            slurm_script += f"singularity exec {container_image} {container_command}\n"
            slurm_script += "echo 'Container execution completed.'\n"
        
        # Capture any output files
        if job.output_files:
            slurm_script += "\n# Capture output files\n"
            for output_file in job.output_files:
                slurm_script += f"if [ -f {output_file} ]; then cp {output_file} {job_dir}/; fi\n"
        
        return slurm_script

    def submit_job(self, job) -> None:
        """Submit a job to SLURM based on job type."""
        workflow = self.submit_workflow(job)
        
        job_name = f"{job.job_type.value}_{job.job_id}"
        work_name = f"{self.name}.{job.job_id}.{job_name}"
        g_param_str = "None"
        
        self.logger.info(f"Submitting SLURM job {work_name} of type {job.job_type.value}")
        
        # Initialize tracking structure
        if job.job_id not in self.running_funcs:
            self.running_funcs[job.job_id] = {"funcs": {}}
        
        if job_name not in self.running_funcs[job.job_id]["funcs"]:
            self.running_funcs[job.job_id]["funcs"][job_name] = {}
        
        if g_param_str not in self.running_funcs[job.job_id]["funcs"][job_name]:
            # Create job directory
            job_dir = self.job_dir / job.job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Handle job type specific preparation
                if job.job_type == JobType.FUNCTION:
                    # Serialize function and parameters for function jobs
                    with open(job_dir / "function.pkl", 'wb') as f:
                        logging.debug(f"Serializing function for job {job.job_id} with {job.function}")
                        pickle.dump(job.function, f)
                    
                    with open(job_dir / "params.pkl", 'wb') as f:
                        pickle.dump(job.params, f)
                    
                    # Create function execution script
                    execution_script = self._create_function_execution_script(job_dir)
                    script_path = job_dir / "execute_function.py"
                    with open(script_path, 'w') as f:
                        f.write(execution_script)
                    script_path.chmod(0o755)
                
                elif job.job_type == JobType.SCRIPT:
                    # For script jobs, save parameters as JSON for potential use
                    with open(job_dir / "params.json", 'w') as f:
                        json.dump(job.params, f, indent=2)
                
                elif job.job_type == JobType.CONTAINER:
                    # For container jobs, save parameters and any additional files
                    with open(job_dir / "params.json", 'w') as f:
                        json.dump(job.params, f, indent=2)
                
                # Create SLURM batch script
                slurm_script = self._create_slurm_script(job, job_dir)
                slurm_path = job_dir / "job.slurm"
                with open(slurm_path, 'w') as f:
                    f.write(slurm_script)
                
                # Submit the job to SLURM
                cmd = ["sbatch", str(slurm_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=job_dir)
                
                if result.returncode != 0:
                    raise Exception(f"sbatch failed: {result.stderr}")
                
                # Extract SLURM job ID
                output_lines = result.stdout.strip().split('\n')
                slurm_job_id = None
                for line in output_lines:
                    if "Submitted batch job" in line:
                        slurm_job_id = line.split()[-1]
                        break
                
                if not slurm_job_id:
                    raise Exception(f"Could not extract SLURM job ID from: {result.stdout}")
                
                # Track the job
                self.jobs[job.job_id] = slurm_job_id
                job.state = JobState.RUNNING
                
                # Store tracking information
                self.running_funcs[job.job_id]["funcs"][job_name][g_param_str] = {
                    "slurm_job_id": slurm_job_id,
                    "job_dir": str(job_dir),
                    "status": "submitted",
                    "results": None,
                    "job_key": work_name,
                    "job_type": job.job_type.value
                }
                
                self.logger.info(f"Submitted SLURM job {slurm_job_id} for work {work_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to submit job {job.job_id}: {str(e)}")
                job.fail(f"SLURM job submission failed: {str(e)}")
        else:
            self.logger.info(f"Work {work_name} already submitted")

    def run_job(self, job) -> None:
        """Run a job using SLURM."""
        self.submit_job(job)

    def check_single_job_status(self, job) -> None:
        """Check the status of a single job."""
        job_name = f"{job.job_type.value}_{job.job_id}"
        g_param_str = "None"
        
        job_info = self.running_funcs.get(job.job_id, {}).get("funcs", {}).get(job_name, {}).get(g_param_str, {})
        
        if not job_info:
            self.logger.error(f"No tracking info found for job {job.job_id}")
            return
        
        slurm_job_id = job_info.get("slurm_job_id")
        job_dir = Path(job_info.get("job_dir"))
        
        if not slurm_job_id:
            self.logger.error(f"No SLURM job ID found for job {job.job_id}")
            return
        
        try:
            # Check if job is still running
            result = subprocess.run(
                ["squeue", "-j", slurm_job_id, "-h"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                job.state = JobState.RUNNING
                return
            
            # Job is no longer in queue, check for completion
            result_path = job_dir / "result.json"
            error_path = job_dir / "error.json"
            
            if result_path.exists():
                try:
                    with open(result_path, 'r') as f:
                        results = json.load(f)
                    
                    self.logger.info(f"Job {job.job_id} completed with results: {results}")
                    job.complete(results)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse result file for job {job.job_id}: {e}")
                    job.fail(f"Failed to parse result file: {e}")
                    
            elif error_path.exists():
                try:
                    with open(error_path, 'r') as f:
                        error_data = json.load(f)
                    
                    error_msg = error_data.get("error", "Unknown error")
                    self.logger.error(f"Job {job.job_id} failed: {error_msg}")
                    job.fail(error_msg)
                    
                except json.JSONDecodeError:
                    job.fail("Job failed and error file is corrupted")
            else:
                # For script/container jobs, check the SLURM output files
                self._check_slurm_output_for_results(job, job_dir)
            
            # Clean up tracking
            if job.job_id in self.running_funcs:
                self.running_funcs.pop(job.job_id, None)
            
        except Exception as e:
            self.logger.error(f"Error checking job {job.job_id}: {e}")

    def _check_slurm_output_for_results(self, job, job_dir: Path):
        """Check SLURM output files for results when no result.json is found."""
        # Look for SLURM output files
        slurm_out_files = list(job_dir.glob("slurm_*.out"))
        
        if slurm_out_files:
            # Try to extract results from SLURM output
            latest_out_file = max(slurm_out_files, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(latest_out_file, 'r') as f:
                    output_content = f.read()
                
                # For script jobs, look for JSON in the output or use exit code
                if "error" in output_content.lower() or "failed" in output_content.lower():
                    job.fail(f"Job failed based on output content")
                else:
                    # Assume success if no obvious errors
                    results = {"stdout": output_content, "status": "completed"}
                    job.complete(results)
                    
            except Exception as e:
                job.fail(f"Could not read SLURM output file: {e}")
        else:
            job.fail("Job completed but no output files found")

    def check_job_status(self, job) -> None:
        """Check the status of a job."""
        if self.num_checks % 60 == 0:
            self.logger.info(f"Checking job {job.job_id} status")
        
        self.check_single_job_status(job)
        self.num_checks += 1

    def cancel_job(self, job) -> None:
        """Cancel a SLURM job."""
        job_name = f"{job.job_type.value}_{job.job_id}"
        g_param_str = "None"
        job_info = self.running_funcs.get(job.job_id, {}).get("funcs", {}).get(job_name, {}).get(g_param_str, {})
        slurm_job_id = job_info.get("slurm_job_id")
        
        if not slurm_job_id:
            self.logger.warning(f"No SLURM job ID found for job {job.job_id}")
            return
        
        try:
            subprocess.run(["scancel", slurm_job_id], check=True)
            job.state = JobState.CANCELLED
            self.running_funcs.pop(job.job_id, None)
            self.logger.info(f"Cancelled SLURM job {slurm_job_id} for {job.job_id}")
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Could not cancel SLURM job {slurm_job_id}: {e}")