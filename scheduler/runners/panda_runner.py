"""
PanDARunner - Runner that submits jobs to the PanDA system.
"""

import os
import time
import json
import pickle
import uuid
from typing import Dict, Any, List, Optional
from ..job.job_state import JobState
from .base_runner import BaseRunner

# Check if PanDA client is available
try:
    from pandaclient import Client
    PANDA_AVAILABLE = True
except ImportError:
    PANDA_AVAILABLE = False


class PanDARunner(BaseRunner):
    """
    A runner that submits jobs to the PanDA system.
    
    This runner requires the PanDA client to be installed.
    """
    
    def __init__(self, 
                 site: str = 'CERN',
                 cloud: str = 'US',
                 queue: str = 'ePIC',
                 vo: str = 'eic',
                 config: Dict[str, Any] = None):
        """
        Initialize a new PanDARunner.
        
        Args:
            site: Site to submit jobs to
            cloud: Cloud to submit jobs to
            queue: Queue to submit jobs to
            vo: Virtual organization
            config: Additional configuration options
        """
        super().__init__(config or {})
        
        if not PANDA_AVAILABLE:
            raise ImportError("PanDA client is not installed. Install with: pip install panda-client")
        
        self.site = site
        self.cloud = cloud
        self.queue = queue
        self.vo = vo
        self.jobs = {}  # job_id -> panda_job_id
        
        # Directory to store job files
        self.job_dir = os.path.expanduser("~/panda_jobs")
        os.makedirs(self.job_dir, exist_ok=True)
        
        # Check PanDA setup
        status, _ = Client.check_panda()
        if not status:
            raise RuntimeError("PanDA client is not properly configured")
    
    def _create_job_files(self, job) -> Dict[str, str]:
        """
        Create necessary files for a PanDA job.
        
        Args:
            job: The job to create files for
            
        Returns:
            Dictionary with paths to job files
        """
        # Create a directory for this job
        job_path = os.path.join(self.job_dir, job.job_id)
        os.makedirs(job_path, exist_ok=True)
        
        # Pickle the job function and parameters
        pickle_path = os.path.join(job_path, 'job.pkl')
        with open(pickle_path, 'wb') as f:
            pickle.dump((job.function, job.params), f)
        
        # Create the job script
        script_path = os.path.join(job_path, 'run.py')
        with open(script_path, 'w') as f:
            f.write("#!/usr/bin/env python\n")
            f.write("import pickle\n")
            f.write("import os\n")
            f.write("import sys\n")
            f.write("import json\n")
            f.write("\n")
            f.write("# Load the job function and parameters\n")
            f.write("with open('job.pkl', 'rb') as f:\n")
            f.write("    function, params = pickle.load(f)\n")
            f.write("\n")
            f.write("# Run the job\n")
            f.write("try:\n")
            f.write("    result = function(**params)\n")
            f.write("    with open('result.json', 'w') as f:\n")
            f.write("        json.dump({\"result\": result}, f)\n")
            f.write("    sys.exit(0)\n")
            f.write("except Exception as e:\n")
            f.write("    with open('error.json', 'w') as f:\n")
            f.write("        json.dump({\"error\": str(e)}, f)\n")
            f.write("    sys.exit(1)\n")
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        return {
            'job_path': job_path,
            'pickle_path': pickle_path,
            'script_path': script_path
        }
    
    def run_job(self, job) -> None:
        """
        Submit a job to PanDA.
        
        Args:
            job: The job to run
        """
        job_files = self._create_job_files(job)
        
        # Prepare job parameters for PanDA
        inFiles = ['job.pkl']
        outFiles = ['result.json', 'error.json']
        
        job_params = {
            'taskName': f'AID2E_{job.job_id}',
            'vo': self.vo,
            'site': self.site,
            'cloud': self.cloud,
            'queue': self.queue,
            'executable': 'run.py',
            'inFiles': inFiles,
            'outFiles': outFiles,
            'fileList': [job_files['pickle_path']],
            'noInput': True,
            'nEvents': 1,
            'nJobs': 1,
            'jobParams': []
        }
        
        # Add any additional options from config
        job_params.update(self.config.get('panda_options', {}))
        
        # Submit the job to PanDA
        try:
            s, o = Client.submitJobs([job_params])
            if s == 0:
                # Job submitted successfully
                panda_job_id = o[0][0]
                self.jobs[job.job_id] = panda_job_id
                job.state = JobState.RUNNING
            else:
                job.fail(f"Failed to submit job to PanDA: {o[0][0]}")
        except Exception as e:
            job.fail(f"Exception submitting job to PanDA: {str(e)}")
    
    def check_job_status(self, job) -> None:
        """
        Check the status of a job and update its state.
        
        Args:
            job: The job to check
        """
        panda_job_id = self.jobs.get(job.job_id)
        if panda_job_id is None:
            return
            
        try:
            # Query PanDA for job status
            s, o = Client.getJobStatus([panda_job_id])
            if s != 0:
                job.fail(f"Failed to check job status: {o}")
                return
                
            panda_status = o[0].jobStatus
            
            # Map PanDA status to our job status
            if panda_status in ['defined', 'assigned', 'activated', 'sent', 'starting']:
                job.state = JobState.QUEUED
            elif panda_status in ['running']:
                job.state = JobState.RUNNING
            elif panda_status in ['finished']:
                # Download output files
                job_path = os.path.join(self.job_dir, job.job_id)
                download_status, download_output = Client.getJobOutput(panda_job_id, job_path)
                
                if download_status != 0:
                    job.fail(f"Failed to download job output: {download_output}")
                    return
                
                # Check for results or errors
                result_path = os.path.join(job_path, 'result.json')
                error_path = os.path.join(job_path, 'error.json')
                
                if os.path.exists(result_path):
                    with open(result_path, 'r') as f:
                        results = json.load(f)
                    job.complete(results)
                elif os.path.exists(error_path):
                    with open(error_path, 'r') as f:
                        error = json.load(f)
                    job.fail(error.get('error', 'Unknown error'))
                else:
                    job.complete({"result": "Job completed but no results found"})
            elif panda_status in ['failed', 'cancelled']:
                job.fail(f"Job failed with PanDA status: {panda_status}")
                
        except Exception as e:
            job.fail(f"Exception checking job status: {str(e)}")
    
    def cancel_job(self, job) -> None:
        """
        Cancel a job.
        
        Args:
            job: The job to cancel
        """
        panda_job_id = self.jobs.get(job.job_id)
        if panda_job_id is None:
            return
            
        try:
            s, o = Client.killJobs([panda_job_id])
            if s == 0:
                job.state = JobState.CANCELLED
                self.jobs.pop(job.job_id, None)
            else:
                pass  # Job might already be completed
        except Exception:
            pass  # Ignore exceptions when cancelling