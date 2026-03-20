from pydantic import BaseModel, validator
from typing import Optional
from config.logging_config import get_logger

logger = get_logger('validator')


class NewsArticle(BaseModel):
    title:       str
    description: Optional[str] = None
    url:         str
    publishedAt: str
    source_name: str

    @validator('title')
    def title_not_empty(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Title too short or empty')
        return v.strip()

    @validator('url')
    def url_valid(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL')
        return v


def validate_articles(articles: list[dict]) -> tuple[list, list]:
    valid, invalid = [], []
    for article in articles:
        try:
            flat = {
                **article,
                'source_name': article.get('source_name') or
                               article.get('source', {}).get('name', ''),
            }
            validated = NewsArticle(**flat)
            valid.append(validated.dict())
        except Exception as e:
            invalid.append({'article': article, 'error': str(e)})
    logger.info(f'Validation: {len(valid)} passed, {len(invalid)} failed')
    return valid, invalid
