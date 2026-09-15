from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class BrandResearchSource(BaseModel):
    title: str
    url: HttpUrl


class BrandResearchResponse(BaseModel):
    brand_name: str
    data_source: Literal["openai_web_search"] = "openai_web_search"
    summary: str = Field(description="带可点击来源链接的 Markdown 摘要，需人工核对。")
    sources: list[BrandResearchSource]
    retrieved_at: datetime
    model: str
    cache_hit: bool = False
    cache_ttl_seconds: int = 600
    needs_review: Literal[True] = True
    saved_to_database: Literal[False] = False
    total_tokens: int | None = Field(default=None, description="原查询的 token 数；缓存命中不会重新调用 AI。")
    web_search_calls: int
