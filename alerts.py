import os, json, requests
from config.logging_config import get_logger

logger = get_logger('alerts')

SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL')

EMOJI = {
    'info':    ':information_source:',
    'warning': ':warning:',
    'error':   ':red_circle:',
}


def send_slack_alert(message: str, level: str = 'warning'):
    if not SLACK_WEBHOOK:
        logger.warning('SLACK_WEBHOOK_URL not set — alert not sent')
        return
    payload = {
        'text': f"{EMOJI.get(level, ':bell:')} *ML Pipeline Alert*\n{message}"
    }
    try:
        response = requests.post(
            SLACK_WEBHOOK,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=5,
        )
        response.raise_for_status()
        logger.info('Slack alert sent')
    except Exception as e:
        logger.error(f'Failed to send Slack alert: {e}')


def alert_drift_detected(dag_id: str, p_value: float):
    send_slack_alert(
        f'Data drift detected in `{dag_id}`\n'
        f'p-value: `{p_value:.4f}` (threshold: 0.05)\n'
        f'Model retrain has been scheduled.',
        level='warning',
    )


def alert_dag_failure(dag_id: str, task_id: str, error: str):
    send_slack_alert(
        f'DAG failure: `{dag_id}` / `{task_id}`\n'
        f'Error: `{error[:300]}`',
        level='error',
    )


def alert_low_validation_rate(valid: int, total: int, threshold: float = 0.8):
    rate = valid / total if total else 0
    if rate < threshold:
        send_slack_alert(
            f'Low validation rate: {valid}/{total} ({rate:.1%})\n'
            f'Threshold: {threshold:.0%} — check ingestion quality.',
            level='warning',
        )
