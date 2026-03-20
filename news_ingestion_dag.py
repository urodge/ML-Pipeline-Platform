from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ingestion.news_client import NewsAPIClient
from src.ingestion.schema import RawArticle
from src.storage.gcs_client import GCSClient
from src.storage.db import load_to_postgres, log_pipeline_run
from config.logging_config import get_logger

logger = get_logger('news_ingestion_dag')

default_args = {
    'owner': 'uddhav',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

GCS_BUCKET = os.getenv('GCS_BUCKET', 'urodge-ml-pipeline-raw')


def fetch_news(**context):
    client = NewsAPIClient()
    raw = client.get_top_headlines(country='in', page_size=100)
    logger.info(f'Fetched {len(raw)} raw articles')
    context['ti'].xcom_push(key='raw_articles', value=raw)


def validate_and_upload(**context):
    raw = context['ti'].xcom_pull(key='raw_articles')
    valid, invalid = [], []
    for article in raw:
        try:
            parsed = RawArticle.from_api_response(article)
            valid.append(parsed.dict())
        except Exception as e:
            invalid.append({'article': article, 'error': str(e)})
    logger.info(f'Validation: {len(valid)} valid, {len(invalid)} invalid')
    # Upload raw valid batch to GCS
    gcs = GCSClient(GCS_BUCKET)
    blob_path = gcs.upload_json(valid, prefix=f"raw/{context['ds']}")
    context['ti'].xcom_push(key='gcs_blob_path', value=blob_path)
    context['ti'].xcom_push(key='valid_count', value=len(valid))


def store_to_postgres(**context):
    raw = context['ti'].xcom_pull(key='raw_articles')
    inserted = load_to_postgres(raw, table='news_raw')
    logger.info(f'Inserted {inserted} rows into news_raw')
    log_pipeline_run(
        dag_id='news_ingestion',
        run_date=context['ds'],
        status='success',
        article_count=inserted,
    )


with DAG(
    dag_id='news_ingestion',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval='@hourly',
    catchup=False,
    tags=['ingestion', 'news'],
) as dag:

    fetch   = PythonOperator(task_id='fetch_news',          python_callable=fetch_news)
    upload  = PythonOperator(task_id='validate_and_upload', python_callable=validate_and_upload)
    store   = PythonOperator(task_id='store_to_postgres',   python_callable=store_to_postgres)

    fetch >> upload >> store
