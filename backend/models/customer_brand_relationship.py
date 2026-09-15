# ============================================================
# Customer Brand Relationship Database Model
# ============================================================

import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey
from backend.database.connection import Base


class CustomerBrandRelationship(Base):
    """
    Customer 与 Brand 之间的关系表。
    """

    __tablename__ = "customer_brand_relationships"


    # Relationship 自己的 UUID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )


    # 指向 customers 表
    customer_id = Column(
        String,
        ForeignKey("customers.id"),
        nullable=False,
    )


    # 指向 brands 表
    brand_id = Column(
        String,
        ForeignKey("brands.id"),
        nullable=False,
    )


    # Customer 与 Brand 是什么关系
    relationship_type = Column(
        String,
        nullable=False,
    )


    # 是否是这个 Brand 的主要合作关系
    is_primary = Column(
        Boolean,
        nullable=False,
        default=False,
    )


    # active / inactive
    status = Column(
        String,
        nullable=False,
        default="active",
    )
