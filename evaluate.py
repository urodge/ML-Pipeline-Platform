import numpy as np
from scipy.stats import ks_2samp
from sklearn.metrics import accuracy_score, f1_score, classification_report
from config.logging_config import get_logger

logger = get_logger('evaluate')


def compute_metrics(y_true: list, y_pred: list) -> dict:
    return {
        'accuracy': round(accuracy_score(y_true, y_pred), 4),
        'f1_score': round(f1_score(y_true, y_pred, average='weighted'), 4),
        'report':   classification_report(y_true, y_pred),
    }


def detect_drift(baseline_scores: list, current_scores: list) -> dict:
    stat, p_value = ks_2samp(baseline_scores, current_scores)
    drift_detected = p_value < 0.05
    result = {
        'drift_detected': drift_detected,
        'ks_statistic':   round(stat, 4),
        'p_value':        round(p_value, 4),
        'mean_baseline':  round(np.mean(baseline_scores), 3),
        'mean_current':   round(np.mean(current_scores), 3),
    }
    if drift_detected:
        logger.warning(f'DATA DRIFT DETECTED — p={p_value:.4f}')
    else:
        logger.info(f'No drift detected — p={p_value:.4f}')
    return result
