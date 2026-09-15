# ============================================================
# Brand Router
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.utils.website import normalize_website_domain

from backend.database.connection import get_db
from backend.models.brand import Brand
from backend.services.brand_lookup import get_brand_by_name

from backend.schemas.brand import (
    BrandCreate,
    BrandResponse,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/brands",
    tags=["Brands"],
)



# ============================================================
# Brand Code
# ============================================================

def generate_brand_code(db: Session):
    """
    自动生成 Brand Code。

    例如：
    DEMO_BRD-000001
    DEMO_BRD-000002
    """

    last_brand = (
        db.query(Brand)
        .order_by(Brand.brand_code.desc())
        .first()
    )

    if last_brand is None:
        next_number = 1

    else:
        last_number = int(
            last_brand.brand_code.split("-")[-1]
        )

        next_number = last_number + 1

    return f"DEMO_BRD-{next_number:06d}"



# ============================================================
# Duplicate Brand Check
# ============================================================

def check_duplicate_brand(
    db: Session,
    brand: BrandCreate,
):
    """
    创建 Brand 前检查明显重复数据。

    当前检查：
    1. Brand Name
    2. Website Domain
    """

    # 1. Brand Name
    existing_brand = (
        db.query(Brand)
        .filter(
            Brand.brand_name.ilike(
                brand.brand_name.strip()
            )
        )
        .first()
    )

    if existing_brand:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Brand already exists",
                "reason": "brand_name_duplicate",
                "existing_brand_id": existing_brand.id,
                "existing_brand_code": existing_brand.brand_code,
                "existing_brand_name": existing_brand.brand_name,
            },
        )

    # 2. Website Domain
    if brand.website:

        new_domain = normalize_website_domain(
            brand.website
        )

        existing_brands = db.query(Brand).all()

        for existing_brand in existing_brands:

            if not existing_brand.website:
                continue

            existing_domain = normalize_website_domain(
                existing_brand.website
            )

            if existing_domain == new_domain:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Brand already exists",
                        "reason": "website_domain_duplicate",
                        "existing_brand_id": existing_brand.id,
                        "existing_brand_code": existing_brand.brand_code,
                        "existing_brand_name": existing_brand.brand_name,
                        "website_domain": new_domain,
                    },
                )


# ============================================================
# Get Brand By Name
# ============================================================

@router.get("/by-name", response_model=BrandResponse)
def get_brand_by_name_endpoint(
    brand_name: str = Query(..., examples=["Northstar"]),
    db: Session = Depends(get_db),
):
    """按品牌名精确查询本地数据；忽略大小写及首尾空格，不联网。"""
    return get_brand_by_name(db, brand_name)


# ============================================================
# Search Brands
# ============================================================

@router.get(
    "/search",
    response_model=list[BrandResponse],
)
def search_brands(
    q: str,
    db: Session = Depends(get_db),
):
    """
    根据关键词查找 Brand。

    可以搜索：
    - Brand Code
    - Brand Name
    - Website
    """

    search = f"%{q.strip()}%"

    brands = (
        db.query(Brand)
        .filter(
            Brand.brand_code.ilike(search)
            | Brand.brand_name.ilike(search)
            | Brand.website.ilike(search)
        )
        .all()
    )

    return brands

# ============================================================
# Create Brand
# ============================================================

@router.post(
    "",
    response_model=BrandResponse,
)
def create_brand(
    brand: BrandCreate,
    db: Session = Depends(get_db),
):
    """
    创建新的 Brand。
    """

    # 1. 检查重复 Brand
    check_duplicate_brand(
        db=db,
        brand=brand,
    )

    # 2. 自动生成 Brand Code
    brand_code = generate_brand_code(db)

    # 3. 创建数据库对象
    db_brand = Brand(
        brand_code=brand_code,
        brand_name=brand.brand_name,
        website=brand.website,
        primary_market=brand.primary_market,
        status=brand.status,
        notes=brand.notes,
    )

    # 4. 保存到数据库
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)

    return db_brand

# ============================================================
# Get All Brands
# ============================================================

@router.get(
    "",
    response_model=list[BrandResponse],
)
def get_brands(
    db: Session = Depends(get_db),
):
    """
    返回数据库中的所有 Brand。
    """

    return db.query(Brand).all()


# ============================================================
# Delete Brand By Brand Code
# ============================================================

@router.delete("/code/{brand_code}")
def delete_brand_by_code(
    brand_code: str,
    db: Session = Depends(get_db),
):
    """
    根据 Brand Code 删除 Brand。

    例如：
    DEMO_BRD-000003
    """

    # 根据 Brand Code 查找
    brand = (
        db.query(Brand)
        .filter(Brand.brand_code == brand_code)
        .first()
    )

    # 找不到 → 返回 404
    if brand is None:
        raise HTTPException(
            status_code=404,
            detail="Brand not found",
        )

    # 删除
    db.delete(brand)
    db.commit()

    return {
        "message": "Brand deleted successfully",
        "brand_code": brand_code,
    }

# ============================================================
# Delete Brand By ID
# ============================================================

@router.delete("/{brand_id}")
def delete_brand(
    brand_id: str,
    db: Session = Depends(get_db),
):
    """
    根据 Brand ID 删除一个品牌。
    """

    # 根据 UUID 查找 Brand
    brand = (
        db.query(Brand)
        .filter(Brand.id == brand_id)
        .first()
    )

    # 找不到 Brand → 返回 404
    if brand is None:
        raise HTTPException(
            status_code=404,
            detail="Brand not found",
        )

    # 先保存信息
    # 因为删除后我们还希望把删除了什么返回给前端
    deleted_brand = {
        "id": brand.id,
        "brand_code": brand.brand_code,
        "brand_name": brand.brand_name,
    }

    # 删除
    db.delete(brand)

    # 正式提交
    db.commit()

    return {
        "message": "Brand deleted successfully",
        "deleted_brand": deleted_brand,
    }

# ============================================================
# Delete All Brands
# ============================================================

@router.delete("")
def delete_all_brands(
    db: Session = Depends(get_db),
):
    """
    删除 Brand 表中的所有品牌。

    注意：
    这是危险操作。
    目前只用于开发和测试。
    """

    # 删除 Brand 表中的所有数据
    deleted_count = db.query(Brand).delete()

    # 正式提交
    db.commit()

    return {
        "message": "All brands deleted successfully",
        "deleted_count": deleted_count,
    }
