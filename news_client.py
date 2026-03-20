import requests, os
from typing import Optional
from config.logging_config import get_logger

logger = get_logger('news_client')


class NewsAPIClient:
    BASE_URL = 'https://newsapi.org/v2'

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        if not self.api_key:
            raise ValueError('NEWS_API_KEY not set')

    def get_top_headlines(
        self,
        country: str = 'in',
        category: Optional[str] = None,
        page_size: int = 100,
    ) -> list[dict]:
        params = {
            'country': country,
            'pageSize': page_size,
            'apiKey': self.api_key,
        }
        if category:
            params['category'] = category
        response = requests.get(
            f'{self.BASE_URL}/top-headlines',
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        articles = response.json().get('articles', [])
        logger.info(f'Fetched {len(articles)} articles (country={country})')
        return articles

    def get_everything(
        self,
        query: str,
        language: str = 'en',
        sort_by: str = 'publishedAt',
        page_size: int = 100,
    ) -> list[dict]:
        params = {
            'q': query,
            'language': language,
            'sortBy': sort_by,
            'pageSize': page_size,
            'apiKey': self.api_key,
        }
        response = requests.get(
            f'{self.BASE_URL}/everything',
            params=params,
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get('articles', [])
