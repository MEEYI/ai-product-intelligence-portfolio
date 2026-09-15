# ============================================================
# Project Model
# ============================================================

import uuid

from sqlalchemy import Column, String, ForeignKey

from backend.database.connection import Base


class Project(Base):
    """
    Project 数据库模型。

    一个 Project 代表一次具体的设计开发任务。
    """

    __tablename__ = "projects"

    # ========================================================
    # Identity
    # ========================================================

    # 数据库内部唯一 ID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # 给员工使用的项目编号
    # 例如：DEMO_PRJ-000001
    project_code = Column(
        String,
        unique=True,
        nullable=False,
    )

    # 项目名称
    project_name = Column(
        String,
        nullable=False,
    )

    # ========================================================
    # Customer / Brand Relationship
    # ========================================================

    # 这个项目属于哪个 Customer
    customer_id = Column(
        String,
        ForeignKey("customers.id"),
        nullable=False,
    )

    # 这个项目是为哪个 Brand 做的
    brand_id = Column(
        String,
        ForeignKey("brands.id"),
        nullable=False,
    )

    # 使用 Customer ↔ Brand 的哪条业务关系
    relationship_id = Column(
        String,
        ForeignKey("customer_brand_relationships.id"),
        nullable=False,
    )

    # ========================================================
    # Project Information
    # ========================================================

    # 目标市场，例如 US / Europe
    target_market = Column(
        String,
        nullable=True,
    )

    # 季节，例如 Demo season
    season = Column(
        String,
        nullable=True,
    )

    # 项目状态
    status = Column(
        String,
        nullable=False,
        default="active",
    )

    # 其他备注
    notes = Column(
        String,
        nullable=True,
    )
