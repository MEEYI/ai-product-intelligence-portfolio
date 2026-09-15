# ============================================================
# Product Reference Model
# ============================================================

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from backend.database.connection import Base


# ============================================================
# Product Reference
# ============================================================

class ProductReference(Base):
    __tablename__ = "product_references"

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # --------------------------------------------------------
    # Relationships
    # --------------------------------------------------------

    brand_id = Column(
        String,
        ForeignKey("brands.id"),
        nullable=False,
    )

    source_id = Column(
        String,
        ForeignKey("brand_sources.id"),
        nullable=False,
    )

    # --------------------------------------------------------
    # Product Information
    # --------------------------------------------------------

    product_name = Column(
        String,
        nullable=False,
    )

    product_url = Column(
        Text,
        nullable=True,
    )

    product_category = Column(
        String,
        nullable=False,
        default="headwear",
    )

    product_type = Column(
        String,
        nullable=True,
    )

    image_url = Column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------------
    # Commercial Signals
    # --------------------------------------------------------

    price = Column(
        Float,
        nullable=True,
    )

    rating = Column(
        Float,
        nullable=True,
    )

    review_count = Column(
        Integer,
        nullable=True,
    )

    is_best_seller = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_new_arrival = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    status = Column(
        String,
        nullable=False,
        default="active",
    )

    notes = Column(
        Text,
        nullable=True,
    )
