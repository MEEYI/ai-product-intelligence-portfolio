# ============================================================
# Project Item Schemas
# ============================================================

from pydantic import BaseModel
from typing import Optional


# ============================================================
# Create Project Item
# ============================================================

class ProjectItemCreate(BaseModel):
    """
    创建 Project Item 时需要提交的数据。
    """

    # 属于哪个 Project
    project_id: str

    # 产品名称
    # 例如：Classic 6-Panel Cap
    item_name: str

    # 产品大类
    # 例如：headwear
    product_category: str = "headwear"

    # 具体帽型
    # 例如：
    # 6_panel / 5_panel / trucker / bucket / beanie
    product_type: str

    # 预计需要多少个设计方案
    design_quantity: int = 20

    # 项目内对这个产品的额外要求
    notes: Optional[str] = None

    # 当前状态
    status: str = "active"


# ============================================================
# Project Item Response
# ============================================================

class ProjectItemResponse(BaseModel):
    """
    API 返回 Project Item 时的数据格式。
    """

    id: str

    # 给员工看的编号
    # 例如 DEMO_ITM-000001
    item_code: str

    project_id: str

    item_name: str
    product_category: str
    product_type: str

    design_quantity: int

    notes: Optional[str] = None
    status: str
