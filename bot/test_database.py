import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from app.database import Base, engine
from app.models.novel import Novel, Chapter, PlotOption

# 加载环境变量
load_dotenv()

def test_database_connection():
    """测试数据库连接"""
    print("\n测试数据库连接...")
    try:
        # 测试连接
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ 数据库连接成功！")
            
        # 创建表
        print("\n创建数据库表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")
        
        # 显示创建的表
        print("\n已创建的表：")
        inspector = inspect(engine)
        for table_name in inspector.get_table_names():
            print(f"- {table_name}")
            columns = inspector.get_columns(table_name)
            for column in columns:
                print(f"  └─ {column['name']}: {column['type']}")
            
    except Exception as e:
        print("❌ 数据库连接失败：", str(e))
        print("\n请确保：")
        print("1. PostgreSQL 服务已启动")
        print("2. 数据库已创建：CREATE DATABASE twitter_novel_bot;")
        print("3. 数据库URL配置正确：", os.getenv("DATABASE_URL"))

if __name__ == "__main__":
    print("开始数据库测试...")
    test_database_connection() 