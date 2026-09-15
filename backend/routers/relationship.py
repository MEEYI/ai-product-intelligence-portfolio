# ============================================================
# Customer Brand Relationship Router
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import get_db

from backend.models.customer import Customer
from backend.models.brand import Brand
from backend.models.customer_brand_relationship import (
    CustomerBrandRelationship,
)

from backend.schemas.customer_brand_relationship import (
    CustomerBrandRelationshipCreate,
    CustomerBrandRelationshipResponse,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/customer-brand-relationships",
    tags=["Customer Brand Relationships"],
)





# ============================================================
# Create Customer Brand Relationship
# ============================================================

@router.post(
    "",
    response_model=CustomerBrandRelationshipResponse,
)
def create_customer_brand_relationship(
    relationship: CustomerBrandRelationshipCreate,
    db: Session = Depends(get_db),
):
    """
    建立 Customer 与 Brand 之间的关系。
    """

    # --------------------------------------------------------
    # 1. 确认 Customer 存在
    # --------------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == relationship.customer_id
        )
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    # --------------------------------------------------------
    # 2. 确认 Brand 存在
    # --------------------------------------------------------

    brand = (
        db.query(Brand)
        .filter(
            Brand.id == relationship.brand_id
        )
        .first()
    )

    if brand is None:
        raise HTTPException(
            status_code=404,
            detail="Brand not found",
        )

    # --------------------------------------------------------
    # 3. 检查 Relationship 是否已经存在
    # --------------------------------------------------------

    existing_relationship = (
        db.query(CustomerBrandRelationship)
        .filter(
            CustomerBrandRelationship.customer_id
            == relationship.customer_id,

            CustomerBrandRelationship.brand_id
            == relationship.brand_id,

            CustomerBrandRelationship.relationship_type
            == relationship.relationship_type,
        )
        .first()
    )

    if existing_relationship:
        raise HTTPException(
            status_code=409,
            detail="Relationship already exists",
        )

    # --------------------------------------------------------
    # 4. 创建 Relationship
    # --------------------------------------------------------

    db_relationship = CustomerBrandRelationship(
        customer_id=relationship.customer_id,
        brand_id=relationship.brand_id,
        relationship_type=relationship.relationship_type,
        is_primary=relationship.is_primary,
        status=relationship.status,
    )

    # --------------------------------------------------------
    # 5. 保存
    # --------------------------------------------------------

    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)

    return db_relationship

# ============================================================
# Get All Customer Brand Relationships
# ============================================================

@router.get(
    "",
    response_model=list[CustomerBrandRelationshipResponse],
)
def get_customer_brand_relationships(
    db: Session = Depends(get_db),
):
    """
    返回所有 Customer 与 Brand 的关系。
    """

    return db.query(CustomerBrandRelationship).all()


# ============================================================
# Delete Customer Brand Relationship
# ============================================================

@router.delete("/{relationship_id}")
def delete_customer_brand_relationship(
    relationship_id: str,
    db: Session = Depends(get_db),
):
    """
    根据 Relationship ID 断开 Customer 与 Brand 的关系。
    """

    # 查找 Relationship
    relationship = (
        db.query(CustomerBrandRelationship)
        .filter(
            CustomerBrandRelationship.id == relationship_id
        )
        .first()
    )

    # 找不到 → 404
    if relationship is None:
        raise HTTPException(
            status_code=404,
            detail="Relationship not found",
        )

    # 先保存一些信息，方便返回
    deleted_relationship = {
        "id": relationship.id,
        "customer_id": relationship.customer_id,
        "brand_id": relationship.brand_id,
        "relationship_type": relationship.relationship_type,
    }

    # 删除关系
    db.delete(relationship)
    db.commit()

    return {
        "message": "Relationship deleted successfully",
        "deleted_relationship": deleted_relationship,
    }
