# ============================================================
# Brand Source Router
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from backend.database.connection import get_db

from backend.models.brand import Brand
from backend.models.brand_source import BrandSource

from backend.schemas.brand_source import (
    BrandSourceCreate,
    BrandSourceResponse,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/brand-sources",
    tags=["Brand Sources"],
)


# ============================================================
# Create Brand Source
# ============================================================

@router.post("", response_model=BrandSourceResponse)
def create_brand_source(
    source: BrandSourceCreate,
    db: Session = Depends(get_db),
):
    """
    创建一个 Brand Source。
    """

    # --------------------------------------------------------
    # 1. 检查 Brand 是否存在
    # --------------------------------------------------------

    brand = (
        db.query(Brand)
        .filter(Brand.id == source.brand_id)
        .first()
    )

    if brand is None:
        raise HTTPException(
            status_code=404,
            detail="Brand not found",
        )

    # --------------------------------------------------------
    # 2. 创建 Brand Source
    # --------------------------------------------------------

    new_source = BrandSource(
        brand_id=source.brand_id,
        source_type=source.source_type,
        source_name=source.source_name,
        source_url=source.source_url,
        auto_collect=source.auto_collect,
        status=source.status,
        notes=source.notes,
    )

    db.add(new_source)
    db.commit()
    db.refresh(new_source)

    return new_source


# ============================================================
# Get All Brand Sources
# ============================================================

@router.get("", response_model=list[BrandSourceResponse])
def get_brand_sources(
    db: Session = Depends(get_db),
):
    """
    获取所有 Brand Sources。
    """

    return db.query(BrandSource).all()


# ============================================================
# Get Brand Sources by Brand
# ============================================================

@router.get(
    "/brand/{brand_id}",
    response_model=list[BrandSourceResponse],
)
def get_brand_sources_by_brand(
    brand_id: str,
    db: Session = Depends(get_db),
):
    """
    获取指定 Brand 的所有 Brand Sources。
    """

    brand = (
        db.query(Brand)
        .filter(Brand.id == brand_id)
        .first()
    )

    if brand is None:
        raise HTTPException(
            status_code=404,
            detail="Brand not found",
        )

    return (
        db.query(BrandSource)
        .filter(BrandSource.brand_id == brand_id)
        .all()
    )


# ============================================================
# Delete Brand Source
# ============================================================

@router.delete("/{source_id}")
def delete_brand_source(
    source_id: str,
    db: Session = Depends(get_db),
):
    """
    删除一个 Brand Source。

    V1 先使用物理删除。
    """

    source = (
        db.query(BrandSource)
        .filter(BrandSource.id == source_id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Brand Source not found",
        )

    deleted_source = {
        "id": source.id,
        "source_name": source.source_name,
    }

    db.delete(source)
    db.commit()

    return {
        "message": "Brand Source deleted successfully",
        "deleted_source": deleted_source,
    }
