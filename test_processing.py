import pytest
from src.processing.cleaner import clean_article, clean_articles
from src.processing.validator import validate_articles

VALID_ARTICLE = {
    'title':       'Markets rally strongly on positive trade data',
    'description': 'Investors reacted positively to the latest figures.',
    'url':         'https://example.com/article/1',
    'publishedAt': '2025-01-15T10:00:00Z',
    'source_name': 'Reuters',
}


# ── Cleaner tests ─────────────────────────────────────────────────────────

def test_clean_removes_html_tags():
    article = {**VALID_ARTICLE, 'title': '<b>Big News Today</b>'}
    result = clean_article(article)
    assert '<b>' not in result['title']
    assert result['title'] == 'Big News Today'


def test_clean_removes_newsapi_truncation():
    article = {**VALID_ARTICLE, 'description': 'Article text [+1234 chars]'}
    result = clean_article(article)
    assert '[+1234 chars]' not in result['description']


def test_clean_collapses_whitespace():
    article = {**VALID_ARTICLE, 'title': 'Too   many   spaces   here'}
    result = clean_article(article)
    assert result['title'] == 'Too many spaces here'


def test_clean_handles_none_description():
    article = {**VALID_ARTICLE, 'description': None}
    result = clean_article(article)
    assert result['description'] == ''


def test_clean_articles_returns_same_count():
    articles = [VALID_ARTICLE, {**VALID_ARTICLE, 'url': 'https://example.com/2'}]
    result = clean_articles(articles)
    assert len(result) == 2


# ── Validator tests ───────────────────────────────────────────────────────

def test_validate_passes_valid_article():
    valid, invalid = validate_articles([VALID_ARTICLE])
    assert len(valid) == 1
    assert len(invalid) == 0


def test_validate_rejects_short_title():
    bad = {**VALID_ARTICLE, 'title': 'Bad'}
    valid, invalid = validate_articles([bad])
    assert len(valid) == 0
    assert len(invalid) == 1


def test_validate_rejects_bad_url():
    bad = {**VALID_ARTICLE, 'url': 'not-a-valid-url'}
    valid, invalid = validate_articles([bad])
    assert len(invalid) == 1


def test_validate_separates_mixed_batch():
    articles = [
        VALID_ARTICLE,
        {**VALID_ARTICLE, 'title': 'x', 'url': 'https://example.com/2'},
        {**VALID_ARTICLE, 'url': 'https://example.com/3'},
    ]
    valid, invalid = validate_articles(articles)
    assert len(valid) == 2
    assert len(invalid) == 1
