from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.model.train import train_sentiment_model
from src.model.evaluate import detect_drift
from src.storage.db import fetch_training_data, fetch_recent_scores, log_pipeline_run
from config.logging_config import get_logger

logger = get_logger('model_retrain_dag')

default_args = {
    'owner': 'uddhav',
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

MODEL_PATH = os.getenv('MODEL_PATH', '/opt/airflow/models/sentiment_model.pkl')


def check_drift(**context):
    baseline = fetch_recent_scores(days=30, table='baseline_scores')
    current  = fetch_recent_scores(days=1,  table='prediction_scores')
    if not baseline or not current:
        logger.info('Not enough data for drift check — skipping')
        context['ti'].xcom_push(key='should_retrain', value=False)
        return
    result = detect_drift(baseline, current)
    logger.info(f'Drift check: {result}')
    context['ti'].xcom_push(key='should_retrain', value=result['drift_detected'])


def retrain_model(**context):
    should_retrain = context['ti'].xcom_pull(key='should_retrain')
    if not should_retrain:
        logger.info('No drift detected — skipping retrain')
        return
    logger.info('Drift detected — starting model retrain')
    texts, labels = fetch_training_data(days=30)
    metrics = train_sentiment_model(texts=texts, labels=labels, model_path=MODEL_PATH)
    logger.info(f'Retrain complete. Metrics: {metrics}')


def log_run(**context):
    log_pipeline_run(
        dag_id='model_retrain',
        run_date=context['ds'],
        status='success',
        metadata={'retrained': context['ti'].xcom_pull(key='should_retrain')},
    )


with DAG(
    dag_id='model_retrain',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['model', 'retrain'],
) as dag:

    drift_check = PythonOperator(task_id='check_drift',   python_callable=check_drift)
    retrain     = PythonOperator(task_id='retrain_model', python_callable=retrain_model)
    log         = PythonOperator(task_id='log_run',       python_callable=log_run)

    drift_check >> retrain >> log
