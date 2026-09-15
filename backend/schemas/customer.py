# ============================================================
# Customer Schema
# ============================================================
#
# 这个文件负责定义：
# API 接收和返回的 Customer 数据格式。
#
# 注意：
# Schema 不是数据库表。
# 它只是规定“数据应该长什么样”。


from pydantic import BaseModel
from typing import Optional


# ============================================================
# 创建 Customer 时使用
# ============================================================

class CustomerCreate(BaseModel):

    # 客户名称
    customer_name: str

    # 客户类型
    #
    # 例如：
    # brand_owner
    # trading_company
    # distributor
    # sourcing_company
    # manufacturer
    # agency
    customer_type: str

    # 国家 / 市场
    country: str

    # 官网
    #
    # 以后我们可以从这里提取 domain，
    # 用来辅助判断重复客户。
    website: Optional[str] = None

    # 公司法定名称
    #
    # 例如：
    # 页面上可能叫 "ABC Trading"
    # 但正式注册名可能是：
    # "ABC Trading Group LLC"
    #
    # V1 可以不填。
    legal_name: Optional[str] = None

    # 公司注册号 / 企业编号
    #
    # 不同国家格式不同，
    # 所以暂时用字符串。
    #
    # 这是未来判断重复客户时非常强的依据。
    registration_number: Optional[str] = None

    # 备注
    notes: Optional[str] = None


# ============================================================
# 返回 Customer 时使用
# ============================================================

class CustomerResponse(BaseModel):

    # 数据库内部真正的唯一 ID
    #
    # 例如：
    # 550e8400-e29b-41d4-a716-446655440000
    id: str

    # 给员工看的业务编号
    #
    # 例如：
    # CUS-000001
    customer_code: str

    customer_name: str

    customer_type: str

    country: str

    website: Optional[str] = None

    legal_name: Optional[str] = None

    registration_number: Optional[str] = None

    notes: Optional[str] = None
