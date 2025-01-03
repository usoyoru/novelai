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
    """Initialize database"""
    Base.metadata.create_all(bind=engine)

def migrate_votes_to_wallet():
    """Migrate vote records from IP address to wallet address"""
    db = SessionLocal()
    try:
        # Check if wallet_address column exists
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'votes' AND column_name = 'wallet_address'"))
        if not result.fetchone():
            # Add wallet_address column
            db.execute(text("ALTER TABLE votes ADD COLUMN wallet_address VARCHAR"))
            # Copy values from ip_address to wallet_address
            db.execute(text("UPDATE votes SET wallet_address = ip_address"))
            # Drop ip_address column
            db.execute(text("ALTER TABLE votes DROP COLUMN ip_address"))
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Migration error: {str(e)}")
    finally:
        db.close() 