import asyncio
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.database import SessionLocal, init_db
from app.models.novel import Novel
from app.services.ai_service import AIService
from app.tasks.novel_tasks import NovelTasks

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./novel_bot.db")
CHECK_INTERVAL = 60  # 每分钟检查一次

async def main():
    """主函数"""
    try:
        # 初始化数据库
        init_db()
        logger.info("数据库初始化完成")
        
        # 创建数据库会话
        db = SessionLocal()
        
        # 创建服务实例
        ai_service = AIService()
        novel_tasks = NovelTasks(db, ai_service)
        
        # 检查是否需要创建新小说
        latest_novel = db.query(Novel).order_by(Novel.created_at.desc()).first()
        
        if not latest_novel:
            logger.info("数据库中没有小说记录，开始创建第一本小说...")
            await novel_tasks.start_new_novel(
                title="Digital Fortune: Crypto Chronicles",
                genre="Crypto Finance"
            )
        else:
            # 检查最后一本小说的创建时间
            now = datetime.now()
            days_diff = (now - latest_novel.created_at.replace(tzinfo=None)).days
            
            if days_diff >= 7:
                logger.info("最后一本小说创建超过7天，开始创建新小说...")
                await novel_tasks.start_new_novel(
                    title="Digital Fortune: Crypto Chronicles",
                    genre="Crypto Finance"
                )
        
        logger.info("启动小说机器人...")
        while True:
            try:
                # 处理已完成的投票
                await novel_tasks.process_completed_polls()
                
                # 等待下一次检查
                await asyncio.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"处理投票时出错: {str(e)}")
                logger.exception("详细错误信息:")
                await asyncio.sleep(CHECK_INTERVAL)
                
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        logger.exception("详细错误信息:")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 