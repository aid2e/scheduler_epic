import pandas as pd
from ax.core.base_trial import BaseTrial
from ax.core.runner import Runner
from ax.core.trial import Trial
from ax.core.metric import Metric, MetricFetchResult, MetricFetchE
from ax.core.data import Data
from ax.utils.common.result import Ok, Err
from joblib_setup import get_joblib_queue_client

## TO-DO: Need to define the evaluation metric
class ScriptExecutionMetric(Metric):  # Pulls data for trial from external system.
    def fetch_trial_data(self, trial: BaseTrial) -> MetricFetchResult:
        if not isinstance(trial, Trial):
            raise ValueError("This metric only handles `Trial`.")

        try:
            joblib_queue = get_joblib_queue_client()
            script_output = joblib_queue.get_outcome_value_for_completed_job(
                job_id=trial.run_metadata.get("job_id")
            )
            df_dict = {
                "trial_index": trial.index,
                "metric_name": "script_execution",
                "arm_name": trial.arm.name,
                "mean": script_output.get("result"),
                "sem": None,
            }
            return Ok(value=Data(df=pd.DataFrame.from_records([df_dict])))
        except Exception as e:
            return Err(
                MetricFetchE(message=f"Failed to fetch {self.name}", exception=e)
            )