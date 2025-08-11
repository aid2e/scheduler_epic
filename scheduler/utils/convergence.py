#!/usr/bin/env python

from typing import Tuple
from ax.modelbridge.modelbridge_utils import observed_hypervolume  # _get_modelbridge_training_data, hypervolume


def cal_single_objective_convergence(ax_client, best_objective_previous, logger) -> Tuple[float, float]:
    """
    Calculate convergence for single-objective optimization.

    Returns:
        A tuple containing:
            - The current best objective value.
            - The relative improvement (convergence value).
    """
    epsilon = 1e-8  # To prevent division by zero

    try:
        best_point = ax_client.get_best_parameters()
    except Exception as e:
        logger.warning(f"Failed to get best parameters: {e}")
        return 0.0, 0.0

    if best_point is None:
        logger.info("No completed trials yet. Skipping convergence calculation.")
        return 0.0, 0.0

    best_parameters, values = best_point
    metric_name = next(iter(values[0].keys()))  # Automatically get the metric name
    best_objective_current = values[0][metric_name]

    if best_objective_previous is None:
        converged = 0.0
    else:
        improvement = abs(best_objective_previous - best_objective_current)
        denominator = abs(best_objective_previous) + epsilon
        converged = improvement / denominator

    return best_objective_current, converged


def cal_hv_convergence(ax_client, hv_pareto: float, trial_index: int = None) -> Tuple[float, float]:
    """
    Calculate hypervolume convergence for multi-objective optimization.

    Args:
        ax_client: AxClient instance.
        hv_pareto: Previous hypervolume value (or None for first iteration).
        trial_index: Index of the current trial.

    Returns:
        (hv, convergence):
            hv: Current hypervolume.
            convergence: Relative improvement over hv_pareto.
    """
    generation_strategy = ax_client.generation_strategy
    modelbridge = generation_strategy.model
    optimization_config = ax_client.experiment.optimization_config
    # objectives = optimization_config.objective.objectives
    thresholds = optimization_config.objective_thresholds

    # print(f"generation_strategy: {generation_strategy}, modelbridge: {modelbridge}")
    if modelbridge is None or not getattr(modelbridge, "outcomes", None):
        # during the sobol stage, SobolGenerator doesn't produce a fitted model, 'outcommes' will
        # be empty and it will fail to calculate hv with observed_hypervolume
        return 0.0, 0.0  # No model yet

    # print(f"hv_pareto: {hv_pareto}")
    # Compute relative convergence
    if hv_pareto is None:
        hv = 0.0
        convergence = 0.0
    else:
        # Compute observed hypervolume
        hv = observed_hypervolume(
            modelbridge=modelbridge,
            objective_thresholds=thresholds,
            optimization_config=optimization_config,
            selected_metrics=None,
        )

        improvement = hv - hv_pareto
        denominator = hv_pareto + 1e-8  # Avoid division by zero
        convergence = improvement / denominator

    return hv, convergence
