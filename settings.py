import os
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).parent.parent
MODELS_DIR = ROOT_DIR / 'models'
MODELS_DIR.mkdir(exist_ok=True)

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://airflow:airflow@localhost:5432/pipeline')

# ── NewsAPI ──────────────────────────────────────────────────────────────────
NEWS_API_KEY  = os.getenv('NEWS_API_KEY')
NEWS_COUNTRY  = os.getenv('NEWS_COUNTRY', 'in')
NEWS_PAGESIZE = int(os.getenv('NEWS_PAGESIZE', '100'))

# ── GCP ──────────────────────────────────────────────────────────────────────
GCS_BUCKET  = os.getenv('GCS_BUCKET', 'urodge-ml-pipeline-raw')
GCP_PROJECT = os.getenv('GCP_PROJECT', '')

# ── Model ────────────────────────────────────────────────────────────────────
MODEL_PATH    = os.getenv('MODEL_PATH', str(MODELS_DIR / 'sentiment_model.pkl'))
MODEL_VERSION = os.getenv('MODEL_VERSION', '1.0.0')

# ── Monitoring ───────────────────────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
DRIFT_THRESHOLD   = float(os.getenv('DRIFT_THRESHOLD', '0.05'))

# ── Validation ───────────────────────────────────────────────────────────────
MIN_TITLE_LENGTH = 5
MIN_VALID_RATE   = 0.8
