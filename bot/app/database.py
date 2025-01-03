from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/novel")
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)

def migrate_votes_to_wallet():
    """将投票记录从IP地址迁移到钱包地址"""
    db = SessionLocal()
    try:
        # 检查是否已经有wallet_address列
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'votes' AND column_name = 'wallet_address'"))
        if not result.fetchone():
            # 添加wallet_address列
            db.execute(text("ALTER TABLE votes ADD COLUMN wallet_address VARCHAR"))
            # 将ip_address的值复制到wallet_address
            db.execute(text("UPDATE votes SET wallet_address = ip_address"))
            # 删除ip_address列
            db.execute(text("ALTER TABLE votes DROP COLUMN ip_address"))
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Migration error: {str(e)}")
    finally:
        db.close() 