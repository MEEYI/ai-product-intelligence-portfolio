# ============================================================
# Project Item Router
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import get_db

from backend.models.project import Project
from backend.models.project_item import ProjectItem

from backend.schemas.project_item import (
    ProjectItemCreate,
    ProjectItemResponse,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/project-items",
    tags=["Project Items"],
)


# ============================================================
# Project Item Code Generator
# ============================================================

def generate_item_code(db: Session):
    """
    自动生成 Project Item 编号。

    例如：
    DEMO_ITM-000001
    DEMO_ITM-000002
    """

    last_item = (
        db.query(ProjectItem)
        .order_by(ProjectItem.item_code.desc())
        .first()
    )

    if last_item is None:
        next_number = 1

    else:
        last_number = int(
            last_item.item_code.split("-")[-1]
        )

        next_number = last_number + 1

    return f"DEMO_ITM-{next_number:06d}"


# ============================================================
# Create Project Item
# ============================================================

@router.post("", response_model=ProjectItemResponse)
def create_project_item(
    item: ProjectItemCreate,
    db: Session = Depends(get_db),
):
    """
    创建一个新的 Project Item。
    """

    # --------------------------------------------------------
    # 1. 检查 Project 是否存在
    # --------------------------------------------------------

    project = (
        db.query(Project)
        .filter(Project.id == item.project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # --------------------------------------------------------
    # 2. 生成 Item Code
    # --------------------------------------------------------

    item_code = generate_item_code(db)

    # --------------------------------------------------------
    # 3. 创建数据库对象
    # --------------------------------------------------------

    new_item = ProjectItem(
        item_code=item_code,
        project_id=item.project_id,
        item_name=item.item_name,
        product_category=item.product_category,
        product_type=item.product_type,
        design_quantity=item.design_quantity,
        status=item.status,
        notes=item.notes,
    )

    # --------------------------------------------------------
    # 4. 保存
    # --------------------------------------------------------

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


# ============================================================
# Get All Project Items
# ============================================================

@router.get("", response_model=list[ProjectItemResponse])
def get_project_items(
    db: Session = Depends(get_db),
):
    """
    获取所有 Project Items。
    """

    return db.query(ProjectItem).all()


# ============================================================
# Get Project Item by ID
# ============================================================

@router.get("/{item_id}", response_model=ProjectItemResponse)
def get_project_item(
    item_id: str,
    db: Session = Depends(get_db),
):
    """
    根据 ID 获取一个 Project Item。
    """

    item = (
        db.query(ProjectItem)
        .filter(ProjectItem.id == item_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Project Item not found",
        )

    return item


# ============================================================
# Delete Project Item
# ============================================================

@router.delete("/{item_id}")
def delete_project_item(
    item_id: str,
    db: Session = Depends(get_db),
):
    """
    根据 ID 删除一个 Project Item。

    V1 暂时使用物理删除。
    正式版本以后改为 archive / soft delete。
    """

    item = (
        db.query(ProjectItem)
        .filter(ProjectItem.id == item_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Project Item not found",
        )

    # 删除之前保存基本信息，
    # 这样删除完成后仍然可以告诉前端删掉了什么。
    deleted_item = {
        "id": item.id,
        "item_code": item.item_code,
        "item_name": item.item_name,
    }

    db.delete(item)
    db.commit()

    return {
        "message": "Project Item deleted successfully",
        "deleted_item": deleted_item,
    }
