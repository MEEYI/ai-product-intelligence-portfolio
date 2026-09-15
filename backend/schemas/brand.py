# ============================================================
# Brand Schema
# ============================================================

from pydantic import BaseModel
from typing import Optional


class BrandCreate(BaseModel):
    """
    创建 Brand 时，前端需要提交的数据。
    """

    brand_name: str
    website: Optional[str] = None
    primary_market: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None


class BrandResponse(BaseModel):
    """
    API 返回 Brand 时使用的数据格式。
    """

    id: str
    brand_code: str

    brand_name: str
    website: Optional[str] = None
    primary_market: Optional[str] = None
    status: str
    notes: Optional[str] = None
