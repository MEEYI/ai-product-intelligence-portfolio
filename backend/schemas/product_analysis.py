# ============================================================
# Product Analysis Schemas
# ============================================================

from typing import Optional

from pydantic import BaseModel


# ============================================================
# Create Product Analysis
# ============================================================

class ProductAnalysisCreate(BaseModel):
    """
    保存一个 Product Reference 的结构化分析结果。

    V1 先允许人工填写。
    后面再让 AI 自动生成。
    """

    product_reference_id: str

    # 产品结构
    product_type: Optional[str] = None
    crown_structure: Optional[str] = None
    visor_shape: Optional[str] = None

    # 视觉特征
    main_color: Optional[str] = None
    secondary_color: Optional[str] = None

    # Logo / Graphic
    logo_treatment: Optional[str] = None
    logo_position: Optional[str] = None

    # 材料和风格
    material_language: Optional[str] = None
    style_tags: Optional[str] = None

    # AI 对结果的可信度
    confidence: Optional[float] = None

    notes: Optional[str] = None


# ============================================================
# Product Analysis Response
# ============================================================

class ProductAnalysisResponse(BaseModel):
    id: str

    product_reference_id: str

    product_type: Optional[str] = None
    crown_structure: Optional[str] = None
    visor_shape: Optional[str] = None

    main_color: Optional[str] = None
    secondary_color: Optional[str] = None

    logo_treatment: Optional[str] = None
    logo_position: Optional[str] = None

    material_language: Optional[str] = None
    style_tags: Optional[str] = None

    confidence: Optional[float] = None

    notes: Optional[str] = None
