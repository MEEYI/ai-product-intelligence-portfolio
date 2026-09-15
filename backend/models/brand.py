# ============================================================
# Brand Database Model
# ============================================================

import uuid

from sqlalchemy import Column, String
from backend.database.connection import Base


class Brand(Base):
    """
    Brand 数据库表。
    """

    __tablename__ = "brands"


    # 数据库内部 UUID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )


    # 给业务人员看的 Brand 编号
    #
    # 例如：
    # DEMO_BRD-000001
    brand_code = Column(
        String,
        unique=True,
        nullable=False,
    )


    # 品牌名称
    brand_name = Column(
        String,
        nullable=False,
    )


    # 品牌官网
    website = Column(
        String,
        nullable=True,
    )


    # 主要市场
    #
    # 例如：
    # US
    # Europe
    # China
    primary_market = Column(
        String,
        nullable=True,
    )


    # 品牌状态
    #
    # 目前：
    # active / inactive
    status = Column(
        String,
        nullable=False,
        default="active",
    )


    # 备注
    notes = Column(
        String,
        nullable=True,
    )
