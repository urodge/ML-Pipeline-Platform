from google.cloud import storage
import json, os
from datetime import datetime
from config.logging_config import get_logger

logger = get_logger('gcs_client')


class GCSClient:
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def upload_json(self, data: list, prefix: str) -> str:
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
        blob_path = f'{prefix}/{timestamp}.json'
        blob = self.bucket.blob(blob_path)
        blob.upload_from_string(
            json.dumps(data, ensure_ascii=False),
            content_type='application/json',
        )
        logger.info(f'Uploaded {len(data)} records to gs://{self.bucket.name}/{blob_path}')
        return blob_path

    def download_json(self, blob_path: str) -> list:
        blob = self.bucket.blob(blob_path)
        data = json.loads(blob.download_as_text())
        logger.info(f'Downloaded {len(data)} records from {blob_path}')
        return data

    def list_blobs(self, prefix: str) -> list[str]:
        blobs = self.client.list_blobs(self.bucket.name, prefix=prefix)
        return [b.name for b in blobs]
