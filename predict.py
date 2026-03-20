from fastapi import APIRouter, HTTPException, Depends
from api.schemas import PredictRequest, PredictResponse, BatchPredictRequest, BatchPredictResponse
from src.model.predict import SentimentPredictor
from src.storage.db import get_connection
from config.logging_config import get_logger

router = APIRouter(prefix='/predict', tags=['Predictions'])
logger = get_logger('routes.predict')

_predictor: SentimentPredictor = None


def get_predictor() -> SentimentPredictor:
    global _predictor
    if _predictor is None:
        _predictor = SentimentPredictor()
    return _predictor


def _save_prediction(result: dict):
    """Persist prediction confidence to DB for drift monitoring."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO prediction_scores (text, sentiment, confidence) VALUES (%s, %s, %s)',
                (result['text'][:500], result['sentiment'], result['confidence'])
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f'Failed to save prediction: {e}')


@router.post('', response_model=PredictResponse)
def predict_single(
    req: PredictRequest,
    predictor: SentimentPredictor = Depends(get_predictor),
):
    result = predictor.predict(req.text)
    _save_prediction(result)
    return result


@router.post('/batch', response_model=BatchPredictResponse)
def predict_batch(
    req: BatchPredictRequest,
    predictor: SentimentPredictor = Depends(get_predictor),
):
    if len(req.texts) > 100:
        raise HTTPException(status_code=400, detail='Max 100 texts per batch')
    results = predictor.predict_batch(req.texts)
    for r in results:
        _save_prediction(r)
    return BatchPredictResponse(results=results, total=len(results))
