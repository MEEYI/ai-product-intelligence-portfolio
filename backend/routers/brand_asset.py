# ============================================================
# Brand Asset Router
# ============================================================

import os
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.brand import Brand
from backend.models.brand_asset import BrandAsset
from backend.schemas.brand_asset import BrandAssetResponse


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/brand-assets",
    tags=["Brand Assets"],
)


# ============================================================
# Upload Settings
# ============================================================

UPLOAD_DIR = "uploads/brand_assets"

ALLOWED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".pdf",
}

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/pdf",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

# 如果上传目录不存在，就自动创建
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# File Validation
# ============================================================

def detect_file_type(file_content: bytes):
    """
    根据文件头判断真实文件类型。
    """

    # PNG
    if file_content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"

    # JPG / JPEG
    if file_content.startswith(b"\xff\xd8\xff"):
        return ".jpg"

    # PDF
    if file_content.startswith(b"%PDF"):
        return ".pdf"

    # WEBP
    if (
        len(file_content) >= 12
        and file_content[0:4] == b"RIFF"
        and file_content[8:12] == b"WEBP"
    ):
        return ".webp"

    return None


# ============================================================
# Create Brand Asset
# ============================================================

@router.post("", response_model=BrandAssetResponse)
async def create_brand_asset(
    brand_id: str = Form(...),
    asset_type: str = Form(...),
    use_for_analysis: bool = Form(True),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    创建 Brand Asset。

    功能：
    - 检查 Brand 是否存在
    - 检查文件扩展名
    - 检查 MIME Type
    - 检查文件大小
    - 检查文件真实内容
    - 保存文件
    - 创建数据库记录
    """

    # --------------------------------------------------------
    # 1. 检查 Brand 是否存在
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

    # --------------------------------------------------------
    # 2. 检查文件名
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing",
        )

    # --------------------------------------------------------
    # 3. 检查扩展名
    # --------------------------------------------------------

    _, extension = os.path.splitext(file.filename)
    extension = extension.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file extension. "
                "Allowed: PNG, JPG, JPEG, WEBP, PDF"
            ),
        )

    # --------------------------------------------------------
    # 4. 检查 MIME Type
    # --------------------------------------------------------

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Allowed: PNG, JPG, JPEG, WEBP, PDF"
            ),
        )

    # --------------------------------------------------------
    # 5. 读取文件
    # --------------------------------------------------------

    file_content = await file.read()

    # --------------------------------------------------------
    # 6. 检查文件大小
    # --------------------------------------------------------

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File is too large. Maximum size is 20 MB",
        )

    # --------------------------------------------------------
    # 7. 检查文件真实内容
    # --------------------------------------------------------

    real_extension = detect_file_type(file_content)

    if real_extension is None:
        raise HTTPException(
            status_code=400,
            detail="File content is invalid or unsupported",
        )

    # JPG 和 JPEG 本质是同一种格式
    extension_for_compare = extension

    if extension_for_compare == ".jpeg":
        extension_for_compare = ".jpg"

    if real_extension != extension_for_compare:
        raise HTTPException(
            status_code=400,
            detail="File extension does not match actual file content",
        )

    # --------------------------------------------------------
    # 8. 生成安全文件名
    # --------------------------------------------------------

    stored_file_name = f"{uuid.uuid4()}{extension}"

    stored_file_path = os.path.join(
        UPLOAD_DIR,
        stored_file_name,
    )

    # --------------------------------------------------------
    # 9. 保存文件
    # --------------------------------------------------------

    with open(stored_file_path, "wb") as saved_file:
        saved_file.write(file_content)

    # --------------------------------------------------------
    # 10. 创建数据库记录
    # --------------------------------------------------------

    new_asset = BrandAsset(
        brand_id=brand_id,
        asset_type=asset_type,

        # 保留用户上传时的原始文件名
        file_name=file.filename,

        # 系统内部实际保存位置
        file_url=stored_file_path,

        use_for_analysis=use_for_analysis,
        notes=notes,
        status="active",
    )

    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    return new_asset



# ============================================================
# Get Brand Assets by Brand ID
# ============================================================

@router.get(
    "/brand/{brand_id}",
    response_model=list[BrandAssetResponse],
)
def get_assets_by_brand(
    brand_id: str,
    db: Session = Depends(get_db),
):
    """
    获取指定 Brand 的所有 Brand Assets。
    """

    # 检查 Brand 是否存在
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

    # 查询这个 Brand 的所有素材
    assets = (
        db.query(BrandAsset)
        .filter(BrandAsset.brand_id == brand_id)
        .all()
    )

    return assets

# ============================================================
# Get AI-Ready Brand Assets
# ============================================================

@router.get(
    "/brand/{brand_id}/analysis",
    response_model=list[BrandAssetResponse],
)
def get_analysis_assets_by_brand(
    brand_id: str,
    db: Session = Depends(get_db),
):
    """
    获取指定 Brand 中允许 AI 分析的有效素材。

    只返回：
    - use_for_analysis = True
    - status = active
    """

    # --------------------------------------------------------
    # 1. 检查 Brand 是否存在
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

    # --------------------------------------------------------
    # 2. 查询允许 AI 使用的素材
    # --------------------------------------------------------

    assets = (
        db.query(BrandAsset)
        .filter(
            BrandAsset.brand_id == brand_id,
            BrandAsset.use_for_analysis == True,
            BrandAsset.status == "active",
        )
        .all()
    )

    return assets

# ============================================================
# Get All Brand Assets
# ============================================================

@router.get("", response_model=list[BrandAssetResponse])
def get_brand_assets(
    db: Session = Depends(get_db),
):
    """
    获取所有 Brand Assets。
    """

    return db.query(BrandAsset).all()


# ============================================================
# Get Brand Asset by ID
# ============================================================

@router.get("/{asset_id}", response_model=BrandAssetResponse)
def get_brand_asset(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """
    根据 ID 获取一个 Brand Asset。
    """

    asset = (
        db.query(BrandAsset)
        .filter(BrandAsset.id == asset_id)
        .first()
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Brand Asset not found",
        )

    return asset


# ============================================================
# Delete Brand Asset
# ============================================================

@router.delete("/{asset_id}")
def delete_brand_asset(
    asset_id: str,
    db: Session = Depends(get_db),
):
    """
    删除一个 Brand Asset。

    当前版本只删除数据库记录。
    暂时不删除本地实际文件。
    """

    asset = (
        db.query(BrandAsset)
        .filter(BrandAsset.id == asset_id)
        .first()
    )

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail="Brand Asset not found",
        )

    deleted_asset = {
        "id": asset.id,
        "brand_id": asset.brand_id,
        "asset_type": asset.asset_type,
        "file_name": asset.file_name,
    }

    db.delete(asset)
    db.commit()

    return {
        "message": "Brand Asset deleted successfully",
        "deleted_asset": deleted_asset,
    }
