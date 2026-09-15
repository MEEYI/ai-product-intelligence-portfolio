# ============================================================
# Project Schemas
# ============================================================

from pydantic import BaseModel
from typing import Optional


# ============================================================
# Create Project
# ============================================================

class ProjectCreate(BaseModel):
    """
    创建新项目时，前端需要提交的数据。
    """

    # 项目名称
    # 例如：
    # Northstar Demo Headwear Project
    project_name: str

    # 这个项目属于哪个 Customer
    customer_id: str

    # 这个项目是为哪个 Brand 做的
    brand_id: str

    # Customer 和 Brand 之间具体是哪条关系
    # 例如 owner / licensee / sourcing_partner
    relationship_id: str

    # 项目主要目标市场
    # 例如 US / Europe / Japan
    target_market: Optional[str] = None

    # 季节或系列
    # 例如 Demo season
    season: Optional[str] = None

    # 项目状态
    # 默认刚创建时是 active
    status: str = "active"

    # 其他备注
    notes: Optional[str] = None


# ============================================================
# Project Response
# ============================================================

class ProjectResponse(BaseModel):
    """
    API 返回 Project 时使用的数据格式。
    """

    # 数据库内部唯一 ID
    id: str

    # 给员工看的业务编号
    # 例如 DEMO_PRJ-000001
    project_code: str

    project_name: str

    customer_id: str
    brand_id: str
    relationship_id: str

    target_market: Optional[str] = None
    season: Optional[str] = None

    status: str
    notes: Optional[str] = None
