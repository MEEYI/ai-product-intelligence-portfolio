# ============================================================
# Brand Asset Schemas
# ============================================================

from pydantic import BaseModel
from typing import Optional


# ============================================================
# Create Brand Asset
# ============================================================

class BrandAssetCreate(BaseModel):
    """
    创建 Brand Asset 时需要提交的数据。

    注意：
    这里暂时只记录文件信息。
    真正的文件上传我们下一步再做。
    """

    # 属于哪个 Brand
    brand_id: str

    # 资产类型
    # 例如：
    # logo
    # brand_guideline
    # lookbook
    # reference_image
    # product_image
    # other
    asset_type: str

    # 原始文件名
    # 例如：
    # northstar_logo.png
    # ss27_lookbook.pdf
    file_name: str

    # 文件存放位置
    # 现在可以先存本地路径
    # 以后可以换成 S3 / Supabase Storage URL
    file_url: str

    # 是否允许 Brand Analyzer 使用
    use_for_analysis: bool = True

    # 备注
    notes: Optional[str] = None

    # 状态
    status: str = "active"


# ============================================================
# Brand Asset Response
# ============================================================

class BrandAssetResponse(BaseModel):
    """
    API 返回 Brand Asset 时的数据格式。
    """

    id: str

    brand_id: str
    asset_type: str
    file_name: str
    file_url: str

    use_for_analysis: bool
    notes: Optional[str] = None
    status: str
