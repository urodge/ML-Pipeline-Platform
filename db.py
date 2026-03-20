import os, json
import psycopg2
from psycopg2.extras import execute_values
from config.logging_config import get_logger

logger = get_logger('db')


def get_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS news_raw (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT,
    url          TEXT UNIQUE,
    source_name  TEXT,
    published_at TEXT,
    ingested_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS news_processed (
    id           SERIAL PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT,
    url          TEXT UNIQUE,
    source_name  TEXT,
    published_at TEXT,
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prediction_scores (
    id          SERIAL PRIMARY KEY,
    text        TEXT,
    sentiment   TEXT,
    confidence  FLOAT,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS baseline_scores (
    id          SERIAL PRIMARY KEY,
    confidence  FLOAT,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id            SERIAL PRIMARY KEY,
    dag_id        TEXT,
    run_date      TEXT,
    status        TEXT,
    metadata      JSONB,
    article_count INT DEFAULT 0,
    run_at        TIMESTAMP DEFAULT NOW()
);
"""


def init_db():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLES_SQL)
    conn.commit()
    conn.close()
    logger.info('Database initialised')


def load_to_postgres(articles: list[dict], table: str = 'news_raw') -> int:
    if not articles:
        return 0
    conn = get_connection()
    rows = [(
        a.get('title', ''),
        a.get('description', ''),
        a.get('url', ''),
        a.get('source_name', ''),
        a.get('publishedAt', ''),
    ) for a in articles]
    sql = f"""
        INSERT INTO {table} (title, description, url, source_name, published_at)
        VALUES %s
        ON CONFLICT (url) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    conn.close()
    logger.info(f'Loaded {len(rows)} rows into {table}')
    return len(rows)


def fetch_training_data(days: int = 30) -> tuple[list, list]:
    from textblob import TextBlob
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT title, description FROM news_processed
            WHERE processed_at > NOW() - INTERVAL '{days} days'
        """)
        rows = cur.fetchall()
    conn.close()
    texts  = [r[0] + ' ' + (r[1] or '') for r in rows]
    labels = [1 if TextBlob(t).sentiment.polarity > 0 else 0 for t in texts]
    return texts, labels


def fetch_recent_scores(days: int = 1, table: str = 'prediction_scores') -> list:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT confidence FROM {table}
            WHERE created_at > NOW() - INTERVAL '{days} days'
        """)
        rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def log_pipeline_run(dag_id: str, run_date: str, status: str,
                     metadata: dict = None, article_count: int = 0):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO pipeline_runs (dag_id, run_date, status, metadata, article_count)
            VALUES (%s, %s, %s, %s, %s)
        """, (dag_id, run_date, status, json.dumps(metadata or {}), article_count))
    conn.commit()
    conn.close()
