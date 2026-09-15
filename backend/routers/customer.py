# ============================================================
# Customer Router
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.utils.website import normalize_website_domain


from backend.database.connection import get_db

from backend.models.customer import Customer

from backend.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
)


# ============================================================
# Router
# ============================================================

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)



# ============================================================
# Customer Code
# ============================================================

def generate_customer_code(db: Session):
    """
    自动生成 Customer Code。

    例如：
    DEMO_CUS-000001
    DEMO_CUS-000002
    """

    last_customer = (
        db.query(Customer)
        .order_by(Customer.customer_code.desc())
        .first()
    )

    if last_customer is None:
        next_number = 1

    else:
        last_number = int(
            last_customer.customer_code.split("-")[-1]
        )

        next_number = last_number + 1

    return f"DEMO_CUS-{next_number:06d}"



# ============================================================
# Duplicate Customer Check
# ============================================================

def check_duplicate_customer(
    db: Session,
    customer: CustomerCreate,
):
    """
    创建 Customer 前检查明显重复的数据。

    当前检查：
    1. 企业注册编号
    2. Website Domain
    """

    # --------------------------------------------------------
    # 1. Registration Number
    # --------------------------------------------------------

    if customer.registration_number:

        existing_customer = (
            db.query(Customer)
            .filter(
                Customer.registration_number
                == customer.registration_number
            )
            .first()
        )

        if existing_customer:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Customer already exists",
                    "reason": "registration_number_duplicate",
                    "existing_customer_id": existing_customer.id,
                    "existing_customer_code": existing_customer.customer_code,
                    "existing_customer_name": existing_customer.customer_name,
                },
            )

    # --------------------------------------------------------
    # 2. Website Domain
    # --------------------------------------------------------

    if customer.website:

        new_domain = normalize_website_domain(
            customer.website
        )

        existing_customers = db.query(Customer).all()

        for existing_customer in existing_customers:

            if not existing_customer.website:
                continue

            existing_domain = normalize_website_domain(
                existing_customer.website
            )

            if existing_domain == new_domain:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Customer already exists",
                        "reason": "website_domain_duplicate",
                        "existing_customer_id": existing_customer.id,
                        "existing_customer_code": existing_customer.customer_code,
                        "existing_customer_name": existing_customer.customer_name,
                        "website_domain": new_domain,
                    },
                )


# ============================================================
# Search Customers
# ============================================================

@router.get(
    "/search",
    response_model=list[CustomerResponse],
)
def search_customers(
    q: str,
    db: Session = Depends(get_db),
):
    """
    根据关键词查找 Customer。

    可以搜索：
    - Customer Code
    - Customer Name
    - Legal Name
    - Registration Number
    - Website
    """

    search = f"%{q.strip()}%"

    customers = (
        db.query(Customer)
        .filter(
            Customer.customer_code.ilike(search)
            | Customer.customer_name.ilike(search)
            | Customer.legal_name.ilike(search)
            | Customer.registration_number.ilike(search)
            | Customer.website.ilike(search)
        )
        .all()
    )

    return customers

# ============================================================
# Create Customer
# ============================================================

@router.post(
    "",
    response_model=CustomerResponse,
)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):
    """
    创建新的 Customer。
    """

    # 1. 检查重复 Customer
    check_duplicate_customer(
        db=db,
        customer=customer,
    )

    # 2. 自动生成 Customer Code
    customer_code = generate_customer_code(db)

    # 3. 创建数据库对象
    db_customer = Customer(
        customer_code=customer_code,
        customer_name=customer.customer_name,
        customer_type=customer.customer_type,
        country=customer.country,
        website=customer.website,
        legal_name=customer.legal_name,
        registration_number=customer.registration_number,
        notes=customer.notes,
    )

    # 4. 保存到数据库
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)

    return db_customer

# ============================================================
# Get All Customers
# ============================================================

@router.get(
    "",
    response_model=list[CustomerResponse],
)
def get_customers(
    db: Session = Depends(get_db),
):
    """
    返回数据库中的所有 Customer。
    """

    return db.query(Customer).all()

# ============================================================
# Delete Customer By Code
# ============================================================

@router.delete("/code/{customer_code}")
def delete_customer_by_code(
    customer_code: str,
    db: Session = Depends(get_db),
):
    """
    根据 Customer Code 删除 Customer。

    例如：
    DEMO_CUS-000003
    """

    customer = (
        db.query(Customer)
        .filter(Customer.customer_code == customer_code)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    db.delete(customer)
    db.commit()

    return {
        "message": "Customer deleted successfully",
        "customer_code": customer_code,
    }

# ============================================================
# Delete Customer By ID
# ============================================================

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str,
    db: Session = Depends(get_db),
):
    """
    根据 Customer ID 删除一个客户。
    """

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    deleted_customer = {
        "id": customer.id,
        "customer_code": customer.customer_code,
        "customer_name": customer.customer_name,
    }

    db.delete(customer)
    db.commit()

    return {
        "message": "Customer deleted successfully",
        "deleted_customer": deleted_customer,
    }

# ============================================================
# Delete All Customers
# ============================================================

@router.delete("")
def delete_all_customers(
    db: Session = Depends(get_db),
):
    """
    删除 Customer 表中的所有客户。

    注意：
    这是危险操作。
    目前只用于开发和测试。
    """

    deleted_count = db.query(Customer).delete()

    db.commit()

    return {
        "message": "All customers deleted successfully",
        "deleted_count": deleted_count,
    }
