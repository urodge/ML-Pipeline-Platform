import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app

client = TestClient(app)

MOCK_PREDICTION = {
    'text':          'Markets rally strongly today',
    'sentiment':     'positive',
    'confidence':    0.87,
    'positive_prob': 0.87,
    'negative_prob': 0.13,
}


# ── Health ────────────────────────────────────────────────────────────────

def test_health_returns_ok():
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'model_loaded' in data
    assert 'version' in data


# ── Single prediction ─────────────────────────────────────────────────────

@patch('api.routes.predict.get_predictor')
@patch('api.routes.predict._save_prediction')
def test_predict_returns_sentiment(mock_save, mock_predictor):
    mock_instance = MagicMock()
    mock_instance.predict.return_value = MOCK_PREDICTION
    mock_predictor.return_value = mock_instance
    response = client.post('/predict', json={'text': 'Markets rally strongly today'})
    assert response.status_code == 200
    data = response.json()
    assert data['sentiment'] in ('positive', 'negative')
    assert 0.0 <= data['confidence'] <= 1.0
    assert 'positive_prob' in data
    assert 'negative_prob' in data


def test_predict_missing_text_returns_422():
    response = client.post('/predict', json={})
    assert response.status_code == 422


def test_predict_empty_text():
    response = client.post('/predict', json={'text': ''})
    # Should either succeed or return validation error — not 500
    assert response.status_code in (200, 422)


# ── Batch prediction ──────────────────────────────────────────────────────

@patch('api.routes.predict.get_predictor')
@patch('api.routes.predict._save_prediction')
def test_batch_predict_returns_results(mock_save, mock_predictor):
    mock_instance = MagicMock()
    mock_instance.predict_batch.return_value = [MOCK_PREDICTION, MOCK_PREDICTION]
    mock_predictor.return_value = mock_instance
    response = client.post('/predict/batch', json={'texts': ['text one', 'text two']})
    assert response.status_code == 200
    data = response.json()
    assert data['total'] == 2
    assert len(data['results']) == 2


@patch('api.routes.predict.get_predictor')
def test_batch_predict_over_limit_returns_400(mock_predictor):
    texts = ['text'] * 101
    response = client.post('/predict/batch', json={'texts': texts})
    assert response.status_code == 400
    assert 'Max 100' in response.json()['detail']
