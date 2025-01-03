import os
import sys
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.app.models.novel import Novel, Chapter, PlotOption, Vote
import subprocess
import signal

def get_database_url():
    """获取数据库URL"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        return DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return "sqlite:///./novel_bot.db"

def clean_database():
    """清理数据库"""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()

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

def start_bot():
    """启动机器人"""
    try:
        print("正在启动机器人...")
        process = subprocess.Popen([sys.executable, "bot/main.py"])
        print(f"机器人已启动 (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"启动机器人时出错: {str(e)}")
        return None

def stop_bot(process):
    """停止机器人"""
    if process:
        try:
            print(f"正在停止机器人 (PID: {process.pid})...")
            os.kill(process.pid, signal.SIGTERM)
            process.wait()
            print("机器人已停止")
        except Exception as e:
            print(f"停止机器人时出错: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="小说机器人管理工具")
    parser.add_argument('action', choices=['clean', 'start', 'stop'], help='要执行的操作')
    
    args = parser.parse_args()
    
    if args.action == 'clean':
        clean_database()
    elif args.action == 'start':
        bot_process = start_bot()
        if bot_process:
            try:
                bot_process.wait()
            except KeyboardInterrupt:
                stop_bot(bot_process)
    elif args.action == 'stop':
        print("请使用Ctrl+C停止机器人")

if __name__ == "__main__":
    main() 