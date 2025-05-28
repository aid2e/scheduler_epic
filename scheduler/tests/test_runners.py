"""
Tests for the runners module.
"""

import unittest
import time
from scheduler.job.job import Job
from scheduler.job.job_state import JobState
from scheduler.runners.joblib_runner import JobLibRunner


class TestJobLibRunner(unittest.TestCase):
    """Tests for the JobLibRunner class."""
    
    def test_run_job_success(self):
        """Test running a job successfully."""
        # Define a simple function to run
        def add(a, b):
            return a + b
        
        # Create a job
        job = Job("test_job_1", add, {"a": 1, "b": 2})
        
        # Create a runner
        runner = JobLibRunner()
        job.set_runner(runner)
        
        # Run the job
        job.run()
        
        # Wait for the job to complete
        max_wait = 5  # seconds
        waited = 0
        while job.state == JobState.RUNNING and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
            runner.check_job_status(job)
        
        # Check that the job completed successfully
        self.assertEqual(job.state, JobState.COMPLETED)
        self.assertEqual(job.get_results()["result"], 3)
    
    def test_run_job_failure(self):
        """Test running a job that fails."""
        # Define a function that raises an exception
        def failing_function():
            raise ValueError("Test error")
        
        # Create a job
        job = Job("test_job_2", failing_function, {})
        
        # Create a runner
        runner = JobLibRunner()
        job.set_runner(runner)
        
        # Run the job
        job.run()
        
        # Wait for the job to complete
        max_wait = 5  # seconds
        waited = 0
        while job.state == JobState.RUNNING and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
            runner.check_job_status(job)
        
        # Check that the job failed
        self.assertEqual(job.state, JobState.FAILED)
        self.assertIn("error", job.get_results())
        self.assertIn("Test error", job.get_results()["error"])
    
    def test_cancel_job(self):
        """Test cancelling a job."""
        # Define a function that takes a long time
        def long_running_function():
            time.sleep(10)
            return "Done"
        
        # Create a job
        job = Job("test_job_3", long_running_function, {})
        
        # Create a runner
        runner = JobLibRunner()
        job.set_runner(runner)
        
        # Run the job
        job.run()
        
        # Cancel the job
        runner.cancel_job(job)
        
        # Check that the job was cancelled
        self.assertEqual(job.state, JobState.CANCELLED)


if __name__ == "__main__":
    unittest.main()