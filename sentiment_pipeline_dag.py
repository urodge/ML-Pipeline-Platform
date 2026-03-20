from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.processing.cleaner import clean_articles
from src.processing.validator import validate_articles
from src.storage.db import load_to_postgres, log_pipeline_run
from src.storage.gcs_client import GCSClient
from config.logging_config import get_logger

logger = get_logger('sentiment_pipeline_dag')

default_args = {
    'owner': 'uddhav',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

GCS_BUCKET = os.getenv('GCS_BUCKET', 'urodge-ml-pipeline-raw')


def read_raw_from_gcs(**context):
    gcs = GCSClient(GCS_BUCKET)
    prefix = f"raw/{context['ds']}/"
    blobs = gcs.list_blobs(prefix)
    if not blobs:
        raise ValueError(f'No raw data found for prefix: {prefix}')
    latest = sorted(blobs)[-1]
    articles = gcs.download_json(latest)
    logger.info(f'Loaded {len(articles)} raw articles from GCS')
    context['ti'].xcom_push(key='raw_articles', value=articles)


def clean_and_validate(**context):
    raw = context['ti'].xcom_pull(key='raw_articles')
    cleaned = clean_articles(raw)
    valid, invalid = validate_articles(cleaned)
    logger.info(f'After cleaning+validation: {len(valid)} valid, {len(invalid)} invalid')
    context['ti'].xcom_push(key='valid_articles', value=valid)
    context['ti'].xcom_push(key='invalid_count', value=len(invalid))


def store_processed(**context):
    valid = context['ti'].xcom_pull(key='valid_articles')
    inserted = load_to_postgres(valid, table='news_processed')
    logger.info(f'Inserted {inserted} rows into news_processed')
    gcs = GCSClient(GCS_BUCKET)
    gcs.upload_json(valid, prefix=f"processed/{context['ds']}")
    log_pipeline_run(
        dag_id='sentiment_pipeline',
        run_date=context['ds'],
        status='success',
        article_count=inserted,
    )


with DAG(
    dag_id='sentiment_pipeline',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval='@hourly',
    catchup=False,
    tags=['processing', 'sentiment'],
) as dag:

    read_raw  = PythonOperator(task_id='read_raw_from_gcs',  python_callable=read_raw_from_gcs)
    clean_val = PythonOperator(task_id='clean_and_validate', python_callable=clean_and_validate)
    store     = PythonOperator(task_id='store_processed',    python_callable=store_processed)

    read_raw >> clean_val >> store
