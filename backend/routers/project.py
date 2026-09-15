# ============================================================
# Project Router
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import get_db

from backend.models.customer import Customer
from backend.models.brand import Brand
from backend.models.customer_brand_relationship import CustomerBrandRelationship
from backend.models.project import Project

from backend.schemas.project import (
    ProjectCreate,
    ProjectResponse,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


# ============================================================
# Project Code Generator
# ============================================================

def generate_project_code(db: Session):
    """
    自动生成 Project 编号。

    例如：
    DEMO_PRJ-000001
    DEMO_PRJ-000002
    """

    # 找到目前编号最大的 Project
    last_project = (
        db.query(Project)
        .order_by(Project.project_code.desc())
        .first()
    )

    # 如果数据库里还没有 Project，从 1 开始
    if last_project is None:
        next_number = 1

    else:
        # DEMO_PRJ-000001
        #          ↓
        #          000001
        last_number = int(
            last_project.project_code.split("-")[-1]
        )

        next_number = last_number + 1

    return f"DEMO_PRJ-{next_number:06d}"


# ============================================================
# Create Project
# ============================================================

@router.post("", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
):
    """
    创建一个新的 Project。
    """

    # --------------------------------------------------------
    # 1. 检查 Customer 是否存在
    # --------------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(Customer.id == project.customer_id)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # --------------------------------------------------------
    # 2. 检查 Brand 是否存在
    # --------------------------------------------------------

    brand = (
        db.query(Brand)
        .filter(Brand.id == project.brand_id)
        .first()
    )

    if brand is None:
        raise HTTPException(
            status_code=404,
            detail="Brand not found",
        )

    # --------------------------------------------------------
    # 3. 检查 Relationship 是否存在
    # --------------------------------------------------------

    relationship = (
        db.query(CustomerBrandRelationship)
        .filter(
            CustomerBrandRelationship.id
            == project.relationship_id
        )
        .first()
    )

    if relationship is None:
        raise HTTPException(
            status_code=404,
            detail="Customer-brand relationship not found",
        )

    # --------------------------------------------------------
    # 4. 检查 Relationship 是否真的属于这个 Customer
    # --------------------------------------------------------

    if relationship.customer_id != project.customer_id:
        raise HTTPException(
            status_code=400,
            detail="Relationship does not belong to this customer",
        )

    # --------------------------------------------------------
    # 5. 检查 Relationship 是否真的属于这个 Brand
    # --------------------------------------------------------

    if relationship.brand_id != project.brand_id:
        raise HTTPException(
            status_code=400,
            detail="Relationship does not belong to this brand",
        )

    # --------------------------------------------------------
    # 6. 生成 Project Code
    # --------------------------------------------------------

    project_code = generate_project_code(db)

    # --------------------------------------------------------
    # 7. 创建数据库对象
    # --------------------------------------------------------

    new_project = Project(
        project_code=project_code,
        project_name=project.project_name,
        customer_id=project.customer_id,
        brand_id=project.brand_id,
        relationship_id=project.relationship_id,
        target_market=project.target_market,
        season=project.season,
        status=project.status,
        notes=project.notes,
    )

    # --------------------------------------------------------
    # 8. 保存到数据库
    # --------------------------------------------------------

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


# ============================================================
# Get All Projects
# ============================================================

@router.get("", response_model=list[ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
):
    """
    获取所有 Project。
    """

    projects = db.query(Project).all()

    return projects


# ============================================================
# Get Project by ID
# ============================================================

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    根据 Project ID 获取一个具体项目。
    """

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    # 找不到 Project
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project

# ============================================================
# Delete Project
# ============================================================

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    根据 Project ID 删除一个项目。

    注意：
    目前 V1 使用物理删除。
    以后正式企业版本会改成 archive / soft delete，
    避免历史设计、反馈、订单数据丢失。
    """

    # --------------------------------------------------------
    # 1. 查找 Project
    # --------------------------------------------------------

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    # Project 不存在
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # --------------------------------------------------------
    # 2. 删除前保存基本信息
    # --------------------------------------------------------

    deleted_project = {
        "id": project.id,
        "project_code": project.project_code,
        "project_name": project.project_name,
    }

    # --------------------------------------------------------
    # 3. 删除 Project
    # --------------------------------------------------------

    db.delete(project)
    db.commit()

    # --------------------------------------------------------
    # 4. 返回删除结果
    # --------------------------------------------------------

    return {
        "message": "Project deleted successfully",
        "deleted_project": deleted_project,
    }
