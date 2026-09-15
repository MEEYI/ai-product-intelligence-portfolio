# ============================================================
# Brand Asset Model
# ============================================================

import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey

from backend.database.connection import Base


class BrandAsset(Base):
    """
    Brand Asset 数据库模型。

    一个 Brand Asset 代表某个品牌的一份资料，
    例如 Logo、Brand Guideline、Lookbook、参考图等。
    """

    __tablename__ = "brand_assets"

    # ========================================================
    # Identity
    # ========================================================

    # 数据库内部唯一 ID
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ========================================================
    # Brand
    # ========================================================

    # 这个 Asset 属于哪个 Brand
    brand_id = Column(
        String,
        ForeignKey("brands.id"),
        nullable=False,
    )

    # ========================================================
    # Asset Information
    # ========================================================

    # 资产类型
    # 例如：
    # logo / brand_guideline / lookbook
    # reference_image / product_image / other
    asset_type = Column(
        String,
        nullable=False,
    )

    # 原始文件名
    file_name = Column(
        String,
        nullable=False,
    )

    # 文件存储位置
    # 现在可以是本地路径
    # 以后可以换成 S3 / Supabase Storage URL
    file_url = Column(
        String,
        nullable=False,
    )

    # 是否允许 Brand Analyzer 使用
    use_for_analysis = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    # ========================================================
    # Status / Notes
    # ========================================================

    notes = Column(
        String,
        nullable=True,
    )

    status = Column(
        String,
        nullable=False,
        default="active",
    )
