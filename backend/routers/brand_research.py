from fastapi import APIRouter, HTTPException, Query, Response

from backend.schemas.brand_research import BrandResearchResponse
from backend.services.brand_research import BrandResearchError, research_brand

router = APIRouter(prefix="/brand-research", tags=["Brand Research (Testing)"])


@router.get("", response_model=BrandResearchResponse, summary="按品牌名联网查询公开资料（测试）")
def get_brand_research(
    response: Response,
    brand_name: str = Query(..., description="品牌名称，例如 Northstar", examples=["Northstar"]),
    refresh: bool = Query(False, description="强制重新联网；会产生新的 API 和搜索用量。"),
):
    """查询公开网页并返回带引用的品牌摘要，供人工审核。

    首次查询使用 OpenAI API 和联网搜索，消耗 API 用量；同名结果在本进程缓存 10 分钟。
    refresh=true 会重新查询。结果不会自动写入 Brand、Brand DNA 或产品资料。
    此接口面向本机测试；部署到公网前需加入身份认证和限流。
    """
    response.headers["Cache-Control"] = "no-store"
    try:
        return research_brand(brand_name, refresh=refresh)
    except BrandResearchError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
