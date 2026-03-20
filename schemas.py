from pydantic import BaseModel
from typing import Optional


class PredictRequest(BaseModel):
    text: str

    class Config:
        json_schema_extra = {
            'example': {'text': 'Markets rally as inflation eases across major economies'}
        }


class PredictResponse(BaseModel):
    text:          str
    sentiment:     str
    confidence:    float
    positive_prob: float
    negative_prob: float


class BatchPredictRequest(BaseModel):
    texts: list[str]


class BatchPredictResponse(BaseModel):
    results: list[PredictResponse]
    total:   int


class HealthResponse(BaseModel):
    status:       str
    model_loaded: bool
    version:      str
