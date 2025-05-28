"""
Tests for the trial module.
"""

import unittest
from unittest.mock import MagicMock
from scheduler.trial.trial import Trial
from scheduler.trial.trial_state import TrialState
from scheduler.job.job import Job
from scheduler.job.job_state import JobState


class TestTrial(unittest.TestCase):
    """Tests for the Trial class."""
    
    def test_trial_initialization(self):
        """Test that a trial is initialized correctly."""
        # Create a trial
        trial = Trial("test_trial", {"param1": 1, "param2": 2})
        
        # Check that the trial was initialized correctly
        self.assertEqual(trial.trial_id, "test_trial")
        self.assertEqual(trial.parameters, {"param1": 1, "param2": 2})
        self.assertEqual(trial.state, TrialState.CREATED)
        self.assertEqual(len(trial.jobs), 0)
    
    def test_add_job(self):
        """Test adding a job to a trial."""
        # Create a trial
        trial = Trial("test_trial", {"param1": 1, "param2": 2})
        
        # Create a job
        job = Job("test_job", lambda: None, {})
        
        # Add the job to the trial
        trial.add_job(job)
        
        # Check that the job was added
        self.assertEqual(len(trial.jobs), 1)
        self.assertEqual(trial.jobs[0], job)
    
    def test_run(self):
        """Test running a trial."""
        # Create a trial
        trial = Trial("test_trial", {"param1": 1, "param2": 2})
        
        # Create a mock job
        job = MagicMock()
        
        # Add the job to the trial
        trial.add_job(job)
        
        # Run the trial
        trial.run()
        
        # Check that the job was run
        job.run.assert_called_once()
        
        # Check that the trial state was updated
        self.assertEqual(trial.state, TrialState.RUNNING)
    
    def test_check_status_running(self):
        """Test checking the status of a running trial."""
        # Create a trial
        trial = Trial("test_trial", {"param1": 1, "param2": 2})
        
        # Create a mock job that's running
        job = MagicMock()
        job.is_running.return_value = True
        job.is_completed.return_value = False
        job.has_failed.return_value = False
        
        # Add the job to the trial
        trial.add_job(job)
        
        # Check the status
        status = trial.check_status()
        
        # Check that the status is correct
        self.assertEqual(status, TrialState.RUNNING)
    
    def test_check_status_completed(self):
        """Test checking the status of a completed trial."""
        # Create a trial
        trial = Trial("test_trial", {"param1": 1, "param2": 2})
        
        # Create a mock job that's completed
        job = MagicMock()
        job.is_running.return_value = False
        job.is_completed.return_value = True
        job.has_failed.return_value = False
        
        # Add the job to the trial
        trial.add_job(job)
        
        # Check the status
        status = trial.check_status()
        
        # Check that the status is correct
        self.assertEqual(status, TrialState.COMPLETED)
    
    def test_check_status_failed(self):
        """Test checking the status of a failed trial."""
        # Create a trial
        trial = Trial("test_trial", {"param1": 1, "param2": 2})
        
        # Create a mock job that's failed
        job = MagicMock()
        job.is_running.return_value = False
        job.is_completed.return_value = False
        job.has_failed.return_value = True
        
        # Add the job to the trial
        trial.add_job(job)
        
        # Check the status
        status = trial.check_status()
        
        # Check that the status is correct
        self.assertEqual(status, TrialState.FAILED)
    
    def test_get_results(self):
        """Test getting results from a trial."""
        # Create a trial
        trial = Trial("test_trial", {"param1": 1, "param2": 2})
        
        # Create mock jobs with results
        job1 = MagicMock()
        job1.is_completed.return_value = True
        job1.get_results.return_value = {"metric1": 1}
        
        job2 = MagicMock()
        job2.is_completed.return_value = True
        job2.get_results.return_value = {"metric2": 2}
        
        # Add the jobs to the trial
        trial.add_job(job1)
        trial.add_job(job2)
        
        # Get the results
        results = trial.get_results()
        
        # Check that the results were combined correctly
        self.assertEqual(results, {"metric1": 1, "metric2": 2})


if __name__ == "__main__":
    unittest.main()