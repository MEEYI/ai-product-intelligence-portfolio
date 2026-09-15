# ============================================================
# Database Connection
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ============================================================
# Database URL
# ============================================================

DATABASE_URL = "sqlite:///./portfolio_demo.db"


# ============================================================
# Database Engine
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)


# ============================================================
# Database Session
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# Base Model
# ============================================================

Base = declarative_base()


# ============================================================
# Database Session Dependency
# ============================================================

def get_db():
    """
    为每个 API 请求提供一个数据库 Session。
    API 请求结束后自动关闭。
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
