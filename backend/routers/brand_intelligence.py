# ============================================================
# Brand Intelligence Router
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from backend.database.connection import get_db

from backend.models.brand import Brand
from backend.models.brand_asset import BrandAsset
from backend.models.brand_source import BrandSource
from backend.models.product_reference import ProductReference
from backend.services.brand_lookup import get_brand_by_name


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/brand-intelligence",
    tags=["Brand Intelligence"],
)


# ============================================================
# Get Brand Evidence By Name
# ============================================================

@router.get("/by-name/evidence")
def get_brand_evidence_by_name(
    brand_name: str = Query(..., examples=["Northstar"]),
    db: Session = Depends(get_db),
):
    """按品牌名汇总本地证据；忽略大小写及首尾空格，不联网。"""
    brand = get_brand_by_name(db, brand_name)
    return build_brand_evidence(db, brand)


# ============================================================
# Get Brand Evidence By ID
# ============================================================

@router.get("/{brand_id}/evidence")
def get_brand_evidence(
    brand_id: str,
    db: Session = Depends(get_db),
):
    """
    整理某个 Brand 当前可供 AI 使用的证据。

    V1 只读取现有数据库数据。
    暂时不调用 AI。
    暂时不自动爬取网站。
    """

    # --------------------------------------------------------
    # 1. 找 Brand
    # --------------------------------------------------------

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

    return build_brand_evidence(db, brand)


def build_brand_evidence(db: Session, brand: Brand):
    """Build the shared evidence payload for both name and ID lookups."""
    brand_id = brand.id

    # --------------------------------------------------------
    # 2. 找 AI 可以使用的 Brand Assets
    # --------------------------------------------------------

    assets = (
        db.query(BrandAsset)
        .filter(
            BrandAsset.brand_id == brand_id,
            BrandAsset.status == "active",
            BrandAsset.use_for_analysis == True,
        )
        .all()
    )

    # --------------------------------------------------------
    # 3. 找 Brand Sources
    # --------------------------------------------------------

    sources = (
        db.query(BrandSource)
        .filter(
            BrandSource.brand_id == brand_id,
            BrandSource.status == "active",
        )
        .all()
    )

    # --------------------------------------------------------
    # 4. 找 Product References
    # --------------------------------------------------------

    products = (
        db.query(ProductReference)
        .filter(
            ProductReference.brand_id == brand_id,
            ProductReference.status == "active",
        )
        .all()
    )

    # --------------------------------------------------------
    # 5. 整理成统一 Evidence
    # --------------------------------------------------------

    return {
        "brand": {
            "id": brand.id,
            "brand_code": brand.brand_code,
            "brand_name": brand.brand_name,
            "website": brand.website,
            "primary_market": brand.primary_market,
        },

        "summary": {
            "asset_count": len(assets),
            "source_count": len(sources),
            "product_count": len(products),
        },

        "assets": [
            {
                "id": asset.id,
                "asset_type": asset.asset_type,
                "file_name": asset.file_name,
                "file_url": asset.file_url,
                "notes": asset.notes,
            }
            for asset in assets
        ],

        "sources": [
            {
                "id": source.id,
                "source_type": source.source_type,
                "source_name": source.source_name,
                "source_url": source.source_url,
            }
            for source in sources
        ],

        "products": [
            {
                "id": product.id,
                "source_id": product.source_id,

                "product_name": product.product_name,
                "product_url": product.product_url,

                "product_category": product.product_category,
                "product_type": product.product_type,

                "image_url": product.image_url,

                "price": product.price,
                "rating": product.rating,
                "review_count": product.review_count,

                "is_best_seller": product.is_best_seller,
                "is_new_arrival": product.is_new_arrival,

                "notes": product.notes,
            }
            for product in products
        ],
    }
