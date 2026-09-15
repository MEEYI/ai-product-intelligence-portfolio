# ============================================================
# Product Reference Router
# ============================================================

import os
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
)
from sqlalchemy.orm import Session

from backend.database.connection import get_db

from backend.models.brand import Brand
from backend.models.brand_source import BrandSource
from backend.models.product_reference import ProductReference

from backend.schemas.product_reference import (
    ProductReferenceCreate,
    ProductReferenceUpdate,
    ProductReferenceResponse,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/product-references",
    tags=["Product References"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_PRODUCT_IMAGE_SIZE = 20 * 1024 * 1024


def _detect_product_image_type(content: bytes) -> tuple[str, str] | None:
    """Check supported file signatures; this is not a full image decoder."""
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png", "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg", "image/jpeg"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp", "image/webp"
    return None


# ============================================================
# Create Product Reference
# ============================================================

@router.post("", response_model=ProductReferenceResponse)
def create_product_reference(
    product: ProductReferenceCreate,
    db: Session = Depends(get_db),
):
    """
    创建一个 Product Reference。
    """

    # --------------------------------------------------------
    # 1. 检查 Brand 是否存在
    # --------------------------------------------------------

    brand = (
        db.query(Brand)
        .filter(Brand.id == product.brand_id)
        .first()
    )

    if brand is None:
        raise HTTPException(
            status_code=404,
            detail="Brand not found",
        )

    # --------------------------------------------------------
    # 2. 检查 Brand Source 是否存在
    # --------------------------------------------------------

    source = (
        db.query(BrandSource)
        .filter(BrandSource.id == product.source_id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Brand Source not found",
        )

    # --------------------------------------------------------
    # 3. 检查 Source 是否真的属于这个 Brand
    # --------------------------------------------------------

    if source.brand_id != product.brand_id:
        raise HTTPException(
            status_code=400,
            detail="Brand Source does not belong to this Brand",
        )

    # --------------------------------------------------------
    # 4. 检查产品是否已经存在
    # --------------------------------------------------------

    if product.product_url:

        existing_product = (
            db.query(ProductReference)
            .filter(
                ProductReference.source_id == product.source_id,
                ProductReference.product_url == product.product_url,
            )
            .first()
        )

        if existing_product:
            raise HTTPException(
                status_code=409,
                detail="Product Reference already exists for this Source",
            )

    # --------------------------------------------------------
    # 5. 创建 Product Reference
    # --------------------------------------------------------

    new_product = ProductReference(
        brand_id=product.brand_id,
        source_id=product.source_id,

        product_name=product.product_name,
        product_url=product.product_url,

        product_category=product.product_category,
        product_type=product.product_type,

        image_url=product.image_url,

        price=product.price,
        rating=product.rating,
        review_count=product.review_count,

        is_best_seller=product.is_best_seller,
        is_new_arrival=product.is_new_arrival,

        status=product.status,
        notes=product.notes,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


# ============================================================
# Get All Product References
# ============================================================

@router.get("", response_model=list[ProductReferenceResponse])
def get_product_references(
    db: Session = Depends(get_db),
):
    """
    获取所有 Product References。
    """

    return db.query(ProductReference).all()


# ============================================================
# Get Product References by Brand
# ============================================================

@router.get(
    "/brand/{brand_id}",
    response_model=list[ProductReferenceResponse],
)
def get_product_references_by_brand(
    brand_id: str,
    db: Session = Depends(get_db),
):
    """
    获取某个 Brand 的所有 Product References。
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
        db.query(ProductReference)
        .filter(ProductReference.brand_id == brand_id)
        .all()
    )


# ============================================================
# Get Product References by Source
# ============================================================

@router.get(
    "/source/{source_id}",
    response_model=list[ProductReferenceResponse],
)
def get_product_references_by_source(
    source_id: str,
    db: Session = Depends(get_db),
):
    """
    获取某个 Source 下的所有 Product References。
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

    return (
        db.query(ProductReference)
        .filter(ProductReference.source_id == source_id)
        .all()
    )

# ============================================================
# Upload Product Reference Image
# ============================================================

@router.post(
    "/{reference_id}/image",
    response_model=ProductReferenceResponse,
)
async def upload_product_reference_image(
    reference_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    给一个已有的 Product Reference 上传主图片。

    V1 规则：
    - 支持 JPG / JPEG / PNG / WEBP
    - 最大 20 MB
    - 本地保存到 uploads/product_references/
    - 一条 Product Reference 暂时只保存一张主图片
    """

    # --------------------------------------------------------
    # 1. 检查 Product Reference 是否存在
    # --------------------------------------------------------

    reference = (
        db.query(ProductReference)
        .filter(ProductReference.id == reference_id)
        .first()
    )

    if reference is None:
        raise HTTPException(
            status_code=404,
            detail="Product Reference not found",
        )

    # --------------------------------------------------------
    # 2. 检查文件扩展名
    # --------------------------------------------------------

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    original_filename = file.filename or ""

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG, PNG and WEBP images are allowed",
        )

    # --------------------------------------------------------
    # 3. 检查 MIME Type
    # --------------------------------------------------------

    allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid image content type",
        )

    # --------------------------------------------------------
    # 4. 读取文件
    # --------------------------------------------------------

    # Bound the application read even when the multipart file is much larger.
    file_content = await file.read(MAX_PRODUCT_IMAGE_SIZE + 1)

    if len(file_content) > MAX_PRODUCT_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image is too large. Maximum size is 20 MB",
        )

    if len(file_content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty",
        )

    detected_type = _detect_product_image_type(file_content)
    canonical_extension = ".jpg" if extension == ".jpeg" else extension
    if detected_type != (canonical_extension, file.content_type):
        raise HTTPException(
            status_code=400,
            detail="Image signature, extension and content type must match",
        )

    # --------------------------------------------------------
    # 5. 创建保存目录
    # --------------------------------------------------------

    project_root = PROJECT_ROOT.resolve()
    upload_directory = project_root / "uploads" / "product_references"
    try:
        # Match the analyzer boundary: neither uploads nor its product directory
        # may redirect through a symlink/junction to another location.
        if upload_directory.resolve() != upload_directory:
            raise ValueError("Redirected upload directory")
        upload_directory.mkdir(parents=True, exist_ok=True)
        if upload_directory.resolve() != upload_directory:
            raise ValueError("Redirected upload directory")
    except (OSError, RuntimeError, ValueError):
        raise HTTPException(status_code=500, detail="Product upload directory is unavailable") from None

    # --------------------------------------------------------
    # 6. 生成唯一文件名
    # --------------------------------------------------------

    stored_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = upload_directory / stored_filename

    # --------------------------------------------------------
    # 7. 保存图片到本地
    # --------------------------------------------------------

    # Exclusive creation prevents overwriting any existing file or file link.
    with file_path.open("xb") as output_file:
        output_file.write(file_content)

    # --------------------------------------------------------
    # 8. 把图片路径写入 Product Reference
    # --------------------------------------------------------

    reference.image_url = file_path.relative_to(project_root).as_posix()

    db.commit()
    db.refresh(reference)

    return reference



# ============================================================
# Delete Product Reference
# ============================================================

@router.delete("/{product_id}")
def delete_product_reference(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    删除一个 Product Reference。

    V1 暂时使用物理删除。
    """

    product = (
        db.query(ProductReference)
        .filter(ProductReference.id == product_id)
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product Reference not found",
        )

    deleted_product = {
        "id": product.id,
        "product_name": product.product_name,
    }

    db.delete(product)
    db.commit()

    return {
        "message": "Product Reference deleted successfully",
        "deleted_product": deleted_product,
    }




# ============================================================
# Update Product Reference
# ============================================================

@router.patch(
    "/{reference_id}",
    response_model=ProductReferenceResponse,
)
def update_product_reference(
    reference_id: str,
    update_data: ProductReferenceUpdate,
    db: Session = Depends(get_db),
):
    """
    修改已有 ProductReference。

    PATCH 的特点：
    只修改用户实际传进来的字段。
    """

    # 1. 先找到 ProductReference
    reference = db.query(ProductReference).filter(
        ProductReference.id == reference_id
    ).first()

    if reference is None:
        raise HTTPException(
            status_code=404,
            detail="Product Reference not found",
        )

    # 2. 只拿用户真正传进来的字段
    changes = update_data.model_dump(
        exclude_unset=True
    )

    # 3. 把这些字段更新到数据库对象
    for field, value in changes.items():
        setattr(reference, field, value)

    # 4. 保存数据库
    db.commit()
    db.refresh(reference)

    return reference
