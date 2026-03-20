from fastapi import FastAPI
from api.routes.predict import router as predict_router
from api.schemas import HealthResponse
from src.model.predict import SentimentPredictor
from config.settings import MODEL_PATH, MODEL_VERSION
from config.logging_config import get_logger
import os

logger = get_logger('api.main')

app = FastAPI(
    title='ML Pipeline — Sentiment API',
    description='Sentiment prediction service powered by a production ML pipeline.',
    version=MODEL_VERSION,
)

app.include_router(predict_router)

_model_loaded = False
try:
    SentimentPredictor(model_path=MODEL_PATH)
    _model_loaded = True
except Exception as e:
    logger.warning(f'Model not loaded at startup: {e}')


@app.get('/health', response_model=HealthResponse, tags=['Health'])
def health():
    return HealthResponse(
        status='ok',
        model_loaded=_model_loaded,
        version=MODEL_VERSION,
    )
