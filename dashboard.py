import streamlit as st
import pandas as pd
import psycopg2
import os

st.set_page_config(page_title='ML Pipeline Monitor', layout='wide')
st.title('ML Pipeline — Live Monitor')


@st.cache_data(ttl=300)
def load_pipeline_runs() -> pd.DataFrame:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    df = pd.read_sql(
        'SELECT * FROM pipeline_runs ORDER BY run_at DESC LIMIT 200',
        conn
    )
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_predictions() -> pd.DataFrame:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    df = pd.read_sql(
        'SELECT * FROM prediction_scores ORDER BY created_at DESC LIMIT 500',
        conn
    )
    conn.close()
    return df


# ── Top metrics ─────────────────────────────────────────────────────────────
try:
    runs = load_pipeline_runs()
    preds = load_predictions()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Total pipeline runs',  len(runs))
    col2.metric('Success rate',         f"{(runs['status'] == 'success').mean():.1%}")
    col3.metric('Avg articles / run',   int(runs['article_count'].mean()) if len(runs) else 0)
    col4.metric('Total predictions',    len(preds))

    st.divider()

    # ── Article ingestion trend ──────────────────────────────────────────────
    st.subheader('Article ingestion over time')
    if not runs.empty:
        chart_data = runs.set_index('run_at')[['article_count']].sort_index()
        st.line_chart(chart_data)

    # ── Prediction sentiment distribution ────────────────────────────────────
    st.subheader('Prediction sentiment distribution')
    if not preds.empty:
        col_a, col_b = st.columns(2)
        sentiment_counts = preds['sentiment'].value_counts()
        col_a.bar_chart(sentiment_counts)
        col_b.metric('Avg confidence', f"{preds['confidence'].mean():.2%}")
        col_b.metric('Positive rate',  f"{(preds['sentiment'] == 'positive').mean():.1%}")

    # ── Recent pipeline runs table ───────────────────────────────────────────
    st.subheader('Recent pipeline runs')
    if not runs.empty:
        st.dataframe(
            runs[['dag_id', 'run_date', 'status', 'article_count', 'run_at']].head(20),
            use_container_width=True,
        )

except Exception as e:
    st.error(f'Could not connect to database: {e}')
    st.info('Make sure DATABASE_URL is set and PostgreSQL is running.')
