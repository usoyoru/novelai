import asyncio
import logging
from sqlalchemy.orm import Session
from app import Base, engine, SessionLocal
from app.services.ai_service import AIService
from app.tasks.novel_tasks import NovelTasks

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """为指定章节生成投票选项"""
    try:
        # 初始化服务
        db = SessionLocal()
        ai_service = AIService()
        novel_tasks = NovelTasks(db, ai_service)
        
        # 为第3章生成投票选项
        await novel_tasks.generate_chapter_with_options(novel_id=1, chapter_number=3)
        
    except Exception as e:
        logger.error(f"生成投票选项时出错: {str(e)}")
        logger.exception("详细错误信息:")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 