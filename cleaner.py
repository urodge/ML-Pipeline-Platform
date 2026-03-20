import re
from config.logging_config import get_logger

logger = get_logger('cleaner')


def _clean_text(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)               # remove HTML tags
    text = re.sub(r'\[\+\d+ chars\]', '', text)        # remove NewsAPI truncation marker
    text = re.sub(r'\s+', ' ', text).strip()           # collapse whitespace
    return text


def clean_article(article: dict) -> dict:
    return {
        **article,
        'title':       _clean_text(article.get('title', '')),
        'description': _clean_text(article.get('description', '')),
        'content':     _clean_text(article.get('content', '')),
    }


def clean_articles(articles: list[dict]) -> list[dict]:
    cleaned = [clean_article(a) for a in articles]
    logger.info(f'Cleaned {len(cleaned)} articles')
    return cleaned
