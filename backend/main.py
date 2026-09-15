# ============================================================
# AI Product Intelligence - Main Backend
# ============================================================

from fastapi import FastAPI

from backend.database.connection import Base, engine

# ============================================================
# models导入
# ============================================================

from backend.models.customer import Customer
from backend.models.brand import Brand
from backend.models.customer_brand_relationship import CustomerBrandRelationship
from backend.models.project import Project
from backend.models.project_item import ProjectItem
from backend.models.brand_asset import BrandAsset
from backend.models.brand_source import BrandSource
from backend.models.product_reference import ProductReference
from backend.models.product_analysis import ProductAnalysis

# ============================================================
# routers导入
# ============================================================

from backend.routers import customer
from backend.routers import brand
from backend.routers import relationship
from backend.routers import project
from backend.routers import project_item
from backend.routers import brand_asset
from backend.routers import brand_source
from backend.routers import product_reference
from backend.routers import brand_intelligence
from backend.routers import brand_research
from backend.routers import product_analysis



# ============================================================
# Database
# ============================================================

# 根据 SQLAlchemy Model 创建尚不存在的数据库表
Base.metadata.create_all(bind=engine)


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="AI Product Intelligence",
    version="0.1.0",
)


# ============================================================
# Routers
# ============================================================

app.include_router(customer.router)
app.include_router(brand.router)
app.include_router(relationship.router)
app.include_router(project.router)
app.include_router(project_item.router)
app.include_router(brand_asset.router)
app.include_router(brand_source.router)
app.include_router(product_reference.router)
app.include_router(brand_intelligence.router)
app.include_router(brand_research.router)
app.include_router(product_analysis.router)

# ============================================================
# Root API
# ============================================================

@app.get("/")
def root():
    """
    检查后端是否正常运行。
    """

    return {
        "system": "AI Product Intelligence",
        "status": "running",
        "version": "0.1.0",
    }
