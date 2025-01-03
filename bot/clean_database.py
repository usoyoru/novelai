import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.novel import Novel, Chapter, PlotOption, Vote

# 创建数据库引擎
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./novel_bot.db")
engine = create_engine(DATABASE_URL)

# 创建会话
Session = sessionmaker(bind=engine)
session = Session()

def clean_database():
    """清理数据库中的所有数据"""
    try:
        # 获取所有小说
        novels = session.query(Novel).all()
        
        if not novels:
            print("数据库中没有小说记录")
            return
            
        print(f"找到 {len(novels)} 本小说:")
        for novel in novels:
            print(f"- {novel.title} (ID: {novel.id})")
            
        confirm = input("确认要删除所有小说数据吗？(y/n): ")
        if confirm.lower() != 'y':
            print("取消操作")
            return
            
        # 删除所有数据
        session.query(Vote).delete()
        session.query(PlotOption).delete()
        session.query(Chapter).delete()
        session.query(Novel).delete()
        
        session.commit()
        print("所有数据已清理完成")
        
    except Exception as e:
        print(f"清理数据库时出错: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clean_database() 