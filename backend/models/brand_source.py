# ============================================================
# Brand Source Model
# ============================================================

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
    Text,
)

from backend.database.connection import Base


# ============================================================
# Brand Source
# ============================================================

class BrandSource(Base):
    __tablename__ = "brand_sources"

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # 属于哪个 Brand
    brand_id = Column(
        String,
        ForeignKey("brands.id"),
        nullable=False,
    )

    # --------------------------------------------------------
    # Source Information
    # --------------------------------------------------------

    source_type = Column(
        String,
        nullable=False,
    )

    source_name = Column(
        String,
        nullable=False,
    )

    source_url = Column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------------
    # Collection Settings
    # --------------------------------------------------------

    auto_collect = Column(
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
