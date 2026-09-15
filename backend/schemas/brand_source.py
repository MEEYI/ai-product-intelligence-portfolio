# ============================================================
# Brand Source Schemas
# ============================================================

from typing import Optional

from pydantic import BaseModel


# ============================================================
# Create Brand Source
# ============================================================

class BrandSourceCreate(BaseModel):
    """
    创建一个 Brand Source 时需要的数据。
    """

    brand_id: str

    # 例如：
    # official_website
    # amazon
    # retailer
    # internal
    source_type: str

    # 给人看的名称
    # 例如：Northstar Official Website
    source_name: str

    # 数据来源地址
    source_url: Optional[str] = None

    # V1 暂时不自动采集
    # 先保留这个开关，为后面 Collector 做准备
    auto_collect: bool = False

    status: str = "active"

    notes: Optional[str] = None


# ============================================================
# Brand Source Response
# ============================================================

class BrandSourceResponse(BaseModel):
    """
    API 返回的 Brand Source 数据。
    """

    id: str
    brand_id: str

    source_type: str
    source_name: str
    source_url: Optional[str] = None

    auto_collect: bool

    status: str
    notes: Optional[str] = None
