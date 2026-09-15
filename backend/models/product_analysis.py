# ============================================================
# Product Analysis Model
# ============================================================

import uuid

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    String,
    Text,
)

from backend.database.connection import Base


# ============================================================
# Product Analysis
# ============================================================

class ProductAnalysis(Base):
    __tablename__ = "product_analyses"

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # --------------------------------------------------------
    # Relationship
    # --------------------------------------------------------

    product_reference_id = Column(
        String,
        ForeignKey("product_references.id"),
        nullable=False,
    )

    # --------------------------------------------------------
    # Product Structure
    # --------------------------------------------------------

    product_type = Column(
        String,
        nullable=True,
    )

    crown_structure = Column(
        String,
        nullable=True,
    )

    visor_shape = Column(
        String,
        nullable=True,
    )

    # --------------------------------------------------------
    # Visual Features
    # --------------------------------------------------------

    main_color = Column(
        String,
        nullable=True,
    )

    secondary_color = Column(
        String,
        nullable=True,
    )

    # --------------------------------------------------------
    # Logo / Graphic
    # --------------------------------------------------------

    logo_treatment = Column(
        String,
        nullable=True,
    )

    logo_position = Column(
        String,
        nullable=True,
    )

    # --------------------------------------------------------
    # Materials / Style
    # --------------------------------------------------------

    material_language = Column(
        Text,
        nullable=True,
    )

    style_tags = Column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------------
    # Analysis Quality
    # --------------------------------------------------------

    confidence = Column(
        Float,
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )
