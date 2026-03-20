import pytest
from unittest.mock import patch, MagicMock
from src.ingestion.news_client import NewsAPIClient
from src.ingestion.schema import RawArticle

SAMPLE_RESPONSE = {
    'articles': [
        {
            'title': 'Markets rise on positive economic data',
            'description': 'Stocks gained after inflation figures came in lower than expected.',
            'url': 'https://example.com/article/1',
            'publishedAt': '2025-01-15T10:00:00Z',
            'source': {'name': 'Reuters'},
            'author': 'John Smith',
            'content': 'Full article content here.',
        }
    ]
}


@patch('requests.get')
def test_get_top_headlines_returns_articles(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: SAMPLE_RESPONSE,
    )
    mock_get.return_value.raise_for_status = MagicMock()
    client = NewsAPIClient(api_key='test_key')
    articles = client.get_top_headlines()
    assert len(articles) == 1
    assert articles[0]['title'] == 'Markets rise on positive economic data'


@patch('requests.get')
def test_api_failure_raises(mock_get):
    mock_get.return_value = MagicMock(status_code=401)
    mock_get.return_value.raise_for_status.side_effect = Exception('401 Unauthorized')
    client = NewsAPIClient(api_key='bad_key')
    with pytest.raises(Exception):
        client.get_top_headlines()


def test_missing_api_key_raises():
    import os
    original = os.environ.pop('NEWS_API_KEY', None)
    with pytest.raises(ValueError, match='NEWS_API_KEY not set'):
        NewsAPIClient()
    if original:
        os.environ['NEWS_API_KEY'] = original


def test_raw_article_schema_valid():
    article = RawArticle.from_api_response(SAMPLE_RESPONSE['articles'][0])
    assert article.title == 'Markets rise on positive economic data'
    assert article.source_name == 'Reuters'
    assert article.url.startswith('https://')


def test_raw_article_schema_rejects_short_title():
    bad = {**SAMPLE_RESPONSE['articles'][0], 'title': 'Bad'}
    with pytest.raises(Exception):
        RawArticle.from_api_response(bad)


def test_raw_article_schema_rejects_invalid_url():
    bad = {**SAMPLE_RESPONSE['articles'][0], 'url': 'not-a-url'}
    with pytest.raises(Exception):
        RawArticle.from_api_response(bad)
