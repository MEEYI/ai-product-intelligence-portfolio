# ============================================================
# Product Analysis Router
# ============================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from backend.database.connection import get_db

from backend.models.product_reference import ProductReference
from backend.models.product_analysis import ProductAnalysis

from backend.schemas.product_analysis import (
    ProductAnalysisCreate,
    ProductAnalysisResponse,
)

from backend.services.product_analyzer import (
    ProductAnalyzerConfigurationError,
    analyze_product,
)

# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/product-analyses",
    tags=["Product Analyses"],
)


# ============================================================
# Create Product Analysis
# ============================================================

@router.post("", response_model=ProductAnalysisResponse)
def create_product_analysis(
    analysis: ProductAnalysisCreate,
    db: Session = Depends(get_db),
):
    """
    创建一个 Product Analysis。
    """

    # --------------------------------------------------------
    # 1. 检查 Product Reference 是否存在
    # --------------------------------------------------------

    product = (
        db.query(ProductReference)
        .filter(
            ProductReference.id == analysis.product_reference_id
        )
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product Reference not found",
        )

    # --------------------------------------------------------
    # 2. V1：一个 Product Reference 只保留一份 Analysis
    # --------------------------------------------------------

    existing_analysis = (
        db.query(ProductAnalysis)
        .filter(
            ProductAnalysis.product_reference_id
            == analysis.product_reference_id
        )
        .first()
    )

    if existing_analysis:
        raise HTTPException(
            status_code=409,
            detail="Product Analysis already exists",
        )

    # --------------------------------------------------------
    # 3. 创建 Product Analysis
    # --------------------------------------------------------

    new_analysis = ProductAnalysis(
        product_reference_id=analysis.product_reference_id,

        product_type=analysis.product_type,
        crown_structure=analysis.crown_structure,
        visor_shape=analysis.visor_shape,

        main_color=analysis.main_color,
        secondary_color=analysis.secondary_color,

        logo_treatment=analysis.logo_treatment,
        logo_position=analysis.logo_position,

        material_language=analysis.material_language,
        style_tags=analysis.style_tags,

        confidence=analysis.confidence,
        notes=analysis.notes,
    )

    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)

    return new_analysis


# ============================================================
# Get All Product Analyses
# ============================================================

@router.get("", response_model=list[ProductAnalysisResponse])
def get_product_analyses(
    db: Session = Depends(get_db),
):
    """
    获取所有 Product Analyses。
    """

    return db.query(ProductAnalysis).all()


# ============================================================
# Get Analysis by Product Reference
# ============================================================

@router.get(
    "/product/{product_reference_id}",
    response_model=ProductAnalysisResponse,
)
def get_product_analysis_by_product(
    product_reference_id: str,
    db: Session = Depends(get_db),
):
    """
    获取指定 Product Reference 的分析结果。
    """

    analysis = (
        db.query(ProductAnalysis)
        .filter(
            ProductAnalysis.product_reference_id
            == product_reference_id
        )
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Product Analysis not found",
        )

    return analysis


# ============================================================
# Delete Product Analysis
# ============================================================

@router.delete("/{analysis_id}")
def delete_product_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
):
    """
    删除一个 Product Analysis。

    V1 暂时使用物理删除。
    """

    analysis = (
        db.query(ProductAnalysis)
        .filter(ProductAnalysis.id == analysis_id)
        .first()
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Product Analysis not found",
        )

    db.delete(analysis)
    db.commit()

    return {
        "message": "Product Analysis deleted successfully",
        "id": analysis_id,
    }

# ============================================================
# AI Analyze Product
# ============================================================

@router.post(
    "/product/{product_reference_id}/analyze",
    response_model=ProductAnalysisResponse,
)
def analyze_product_with_ai(
    product_reference_id: str,
    db: Session = Depends(get_db),
):
    """
    使用 AI 分析 Product Reference，
    并把结果保存为 Product Analysis。
    """

    # --------------------------------------------------------
    # 1. 找 Product Reference
    # --------------------------------------------------------

    product = (
        db.query(ProductReference)
        .filter(
            ProductReference.id == product_reference_id
        )
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product Reference not found",
        )

    # --------------------------------------------------------
    # 2. 检查是否已经分析过
    # --------------------------------------------------------

    existing_analysis = (
        db.query(ProductAnalysis)
        .filter(
            ProductAnalysis.product_reference_id
            == product_reference_id
        )
        .first()
    )

    if existing_analysis:
        raise HTTPException(
            status_code=409,
            detail="Product Analysis already exists",
        )

    # --------------------------------------------------------
    # 3. 调用 AI
    # --------------------------------------------------------

    try:
        result = analyze_product(
            product_name=product.product_name,
            product_type=product.product_type,
            image_url=product.image_url,
        )

    except ProductAnalyzerConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail="Configure OPENAI_API_KEY and OPENAI_MODEL before using AI features.",
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="AI analysis failed. Check the input and local configuration, then retry.",
        ) from error

    # --------------------------------------------------------
    # 4. 保存分析结果
    # --------------------------------------------------------

    new_analysis = ProductAnalysis(
        product_reference_id=product.id,

        product_type=result.get("product_type"),
        crown_structure=result.get("crown_structure"),
        visor_shape=result.get("visor_shape"),

        main_color=result.get("main_color"),
        secondary_color=result.get("secondary_color"),

        logo_treatment=result.get("logo_treatment"),
        logo_position=result.get("logo_position"),

        material_language=result.get("material_language"),
        style_tags=result.get("style_tags"),

        confidence=result.get("confidence"),

        notes="Generated by AI Product Analyzer",
    )

    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)

    return new_analysis
