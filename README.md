# ml-pipeline-platform

Production-grade ML pipeline: live news ingestion → cloud storage → sentiment model training → FastAPI prediction serving.  
Fully orchestrated with Apache Airflow and containerized with Docker.

Built to demonstrate end-to-end ML engineering — not just model training, but the full production system around it.

---

## Architecture

```
NewsAPI → Airflow DAG → Pydantic Validation → GCS (raw)
                                  ↓
                        PostgreSQL (processed)
                                  ↓
                  Model Training (Scikit-learn + TF-IDF)
                                  ↓
                  FastAPI Prediction Endpoint (:8000)
                                  ↓
                  Streamlit Monitoring Dashboard (:8501)
```

---

## Tech Stack

| Layer             | Technology                         |
|-------------------|------------------------------------|
| Orchestration     | Apache Airflow 2.8                 |
| Cloud Storage     | GCP Cloud Storage                  |
| Database          | PostgreSQL 15                      |
| Data Validation   | Pydantic v2                        |
| ML Model          | Scikit-learn (TF-IDF + Logistic Regression) |
| Model Serving     | FastAPI + Uvicorn                  |
| Containerization  | Docker + Docker Compose            |
| Monitoring        | Streamlit + structured JSON logging|
| Drift Detection   | SciPy KS-test                      |
| Alerts            | Slack webhooks                     |
| Language          | Python 3.11                        |

---

## How to run locally

```bash
git clone https://github.com/urodge/ml-pipeline-platform
cd ml-pipeline-platform

# 1. Set up environment variables
cp .env.example .env
# Edit .env — add your NEWS_API_KEY and GCP credentials

# 2. Start all services
docker-compose -f docker/docker-compose.yml up --build

# 3. Initialise the database (first time only)
docker exec -it <api_container> python -c "from src.storage.db import init_db; init_db()"
```

Open:
- **Airflow UI** → http://localhost:8080  (admin / admin)
- **API docs**   → http://localhost:8000/docs
- **Dashboard**  → http://localhost:8501

---

## Project structure

```
ml-pipeline-platform/
├── dags/                     Airflow DAG definitions
│   ├── news_ingestion_dag.py       Hourly news fetch → GCS
│   ├── sentiment_pipeline_dag.py   GCS → clean → PostgreSQL
│   └── model_retrain_dag.py        Daily drift check + retrain
├── src/
│   ├── ingestion/            NewsAPI client + Pydantic schema
│   ├── processing/           Text cleaning + validation
│   ├── model/                Train, predict, evaluate
│   └── storage/              GCS client + PostgreSQL helpers
├── api/                      FastAPI prediction service
├── monitoring/               Streamlit dashboard + Slack alerts
├── tests/                    Unit tests (pytest)
├── docker/                   Dockerfiles + docker-compose
├── config/                   Settings + JSON logging
├── models/                   Saved model artefacts (gitignored)
├── requirements.txt
├── .env.example
└── README.md
```

---

## API endpoints

| Method | Endpoint         | Description                  |
|--------|------------------|------------------------------|
| GET    | `/health`        | Service health + model status|
| POST   | `/predict`       | Single text sentiment        |
| POST   | `/predict/batch` | Batch prediction (max 100)   |

**Example request:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "Markets rally as inflation eases"}'
```

**Example response:**
```json
{
  "text": "Markets rally as inflation eases",
  "sentiment": "positive",
  "confidence": 0.87,
  "positive_prob": 0.87,
  "negative_prob": 0.13
}
```

---

## Pipeline phases

| Phase | What's built                            | Status |
|-------|-----------------------------------------|--------|
| 1     | Airflow DAG + NewsAPI ingestion         | ✅     |
| 2     | GCS cloud storage + Pydantic validation | ✅     |
| 3     | Sentiment model + FastAPI + Docker      | ✅     |
| 4     | Monitoring dashboard + drift detection  | ✅     |

---

## Running tests

```bash
pip install pytest pytest-cov httpx
pytest tests/ -v --cov=src --cov=api
```

---

## Author

Uddhav Rodge — AI & ML Engineer  
[github.com/urodge](https://github.com/urodge) · [linkedin.com/in/uddhav-rodge-1501b7274](https://linkedin.com/in/uddhav-rodge-1501b7274)
