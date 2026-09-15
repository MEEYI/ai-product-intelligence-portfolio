# ============================================================
# Project Item Model
# ============================================================

import uuid

from sqlalchemy import Column, String, Integer, ForeignKey

from backend.database.connection import Base


class ProjectItem(Base):
    """
    Project Item 数据库模型。

    一个 Project Item 代表 Project 里面的一项具体产品开发任务。

    例如：
    Project = Northstar SS27 Headwear

    Project Items:
    - 6-Panel Baseball Cap
    - Trucker Cap
    - Bucket Hat
    """

    __tablename__ = "project_items"

    # ========================================================
    # Identity
    # ========================================================

    # 数据库内部唯一 ID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # 给员工看的业务编号
    # 例如：DEMO_ITM-000001
    item_code = Column(
        String,
        unique=True,
        nullable=False,
    )

    # ========================================================
    # Project
    # ========================================================

    # 这个 Item 属于哪个 Project
    project_id = Column(
        String,
        ForeignKey("projects.id"),
        nullable=False,
    )

    # ========================================================
    # Product Information
    # ========================================================

    # 产品名称
    # 例如：Classic 6-Panel Cap
    item_name = Column(
        String,
        nullable=False,
    )

    # 产品大类
    # 例如：headwear
    product_category = Column(
        String,
        nullable=False,
        default="headwear",
    )

    # 具体产品类型
    # 例如：6_panel / trucker / bucket
    product_type = Column(
        String,
        nullable=False,
    )

    # 希望生成多少个设计方案
    design_quantity = Column(
        Integer,
        nullable=False,
        default=20,
    )

    # ========================================================
    # Status / Notes
    # ========================================================

    status = Column(
        String,
        nullable=False,
        default="active",
    )

    notes = Column(
        String,
        nullable=True,
    )
