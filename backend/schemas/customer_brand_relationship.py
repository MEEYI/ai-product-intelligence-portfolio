# ============================================================
# Customer Brand Relationship Schema
# ============================================================

from pydantic import BaseModel


class CustomerBrandRelationshipCreate(BaseModel):
    """
    创建 Customer 与 Brand 关系时提交的数据。
    """

    customer_id: str
    brand_id: str

    # 例如：
    # owner
    # agent
    # distributor
    # licensee
    # sourcing_partner
    # manufacturer
    # other
    relationship_type: str

    is_primary: bool = False
    status: str = "active"


class CustomerBrandRelationshipResponse(BaseModel):
    """
    API 返回 Relationship 时的数据格式。
    """

    id: str
    customer_id: str
    brand_id: str
    relationship_type: str
    is_primary: bool
    status: str
