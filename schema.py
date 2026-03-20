from pydantic import BaseModel, validator, Field
from typing import Optional


class RawArticle(BaseModel):
    title:       str
    description: Optional[str] = None
    content:     Optional[str] = None
    url:         str
    publishedAt: str
    source_name: str = Field(default='')
    author:      Optional[str] = None

    @validator('title')
    def title_not_empty(cls, v):
        v = v.strip()
        if len(v) < 5:
            raise ValueError('Title too short')
        return v

    @validator('url')
    def url_has_scheme(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Invalid URL')
        return v

    @classmethod
    def from_api_response(cls, raw: dict) -> 'RawArticle':
        """Flatten nested source field from NewsAPI response."""
        return cls(
            title=raw.get('title', ''),
            description=raw.get('description'),
            content=raw.get('content'),
            url=raw.get('url', ''),
            publishedAt=raw.get('publishedAt', ''),
            source_name=raw.get('source', {}).get('name', ''),
            author=raw.get('author'),
        )
