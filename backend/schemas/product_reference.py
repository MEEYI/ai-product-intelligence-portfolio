# ============================================================
# Product Reference Schemas
# ============================================================

from typing import Optional

from pydantic import BaseModel


# ============================================================
# Create Product Reference
# ============================================================

class ProductReferenceCreate(BaseModel):
    """
    创建一个 Product Reference 时需要的数据。
    """

    # 属于哪个品牌
    brand_id: str

    # 来自哪个数据源
    source_id: str

    # 产品基本信息
    product_name: str
    product_url: Optional[str] = None

    # 例如：
    # headwear
    product_category: str = "headwear"

    # 例如：
    # 6_panel
    # trucker
    # bucket
    # boonie
    product_type: Optional[str] = None

    # V1 先保存一个主图地址
    image_url: Optional[str] = None

    # 商业信息
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None

    # 商业 / 时间信号
    is_best_seller: bool = False
    is_new_arrival: bool = False

    status: str = "active"

    notes: Optional[str] = None



# ============================================================
# Product Reference Update
# ============================================================

class ProductReferenceUpdate(BaseModel):
    """
    修改已有 ProductReference。

    所有字段都设为 Optional，
    因为 PATCH 只修改用户传进来的字段。
    """

    product_name: Optional[str] = None
    product_url: Optional[str] = None

    product_category: Optional[str] = None
    product_type: Optional[str] = None

    image_url: Optional[str] = None

    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None

    is_best_seller: Optional[bool] = None
    is_new_arrival: Optional[bool] = None

    status: Optional[str] = None
    notes: Optional[str] = None

# ============================================================
# Product Reference Response
# ============================================================

class ProductReferenceResponse(BaseModel):
    """
    API 返回的 Product Reference。
    """

    id: str

    brand_id: str
    source_id: str

    product_name: str
    product_url: Optional[str] = None

    product_category: str
    product_type: Optional[str] = None

    image_url: Optional[str] = None

    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None

    is_best_seller: bool
    is_new_arrival: bool

    status: str
    notes: Optional[str] = None
