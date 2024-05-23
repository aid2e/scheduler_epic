from collections import defaultdict
from typing import Any, Dict, Iterable, Set

from ax.core.base_trial import BaseTrial
from ax.core.runner import Runner
from ax.core.trial import Trial
from ax.core.base_trial import TrialStatus
from joblib_setup import get_joblib_queue_client, run_script



class JoblibJobRunner(Runner):  # Deploys trials to external system.
    def run(self, trial: BaseTrial) -> Dict[str, Any]:
        if not isinstance(trial, Trial):
            raise ValueError("This runner only handles `Trial`.")

        joblib_queue = get_joblib_queue_client()
        job_id = joblib_queue.schedule_job_with_parameters(
            trial.arm.parameters['script_path'],
            trial.arm.parameters['root_file']
        )

        return {"job_id": job_id}

    def poll_trial_status(
        self, trials: Iterable[BaseTrial]
    ) -> Dict[TrialStatus, Set[int]]:

        status_dict = defaultdict(set)
        joblib_queue = get_joblib_queue_client()
        for trial in trials:
            status = joblib_queue.get_job_status(
                job_id=trial.run_metadata.get("job_id")
            )
            status_dict[status].add(trial.index)

        return status_dict
