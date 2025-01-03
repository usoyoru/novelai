import asyncio
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.database import SessionLocal, init_db
from app.models.novel import Novel
from app.services.ai_service import AIService
from app.tasks.novel_tasks import NovelTasks

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./novel_bot.db")
CHECK_INTERVAL = 60  # Check every minute

async def main():
    """Main function"""
    try:
        # Initialize database
        init_db()
        logger.info("Database initialization completed")
        
        # Create database session
        db = SessionLocal()
        
        # Create service instances
        ai_service = AIService()
        novel_tasks = NovelTasks(db, ai_service)
        
        # Check if need to create new novel
        latest_novel = db.query(Novel).order_by(Novel.created_at.desc()).first()
        
        if not latest_novel:
            logger.info("No novels found in database, creating first novel...")
            await novel_tasks.start_new_novel(
                title="Digital Fortune: Crypto Chronicles",
                genre="Crypto Finance"
            )
        else:
            # Check last novel's creation time
            now = datetime.now()
            days_diff = (now - latest_novel.created_at.replace(tzinfo=None)).days
            
            if days_diff >= 7:
                logger.info("Last novel created over 7 days ago, creating new novel...")
                await novel_tasks.start_new_novel(
                    title="Digital Fortune: Crypto Chronicles",
                    genre="Crypto Finance"
                )
        
        logger.info("Starting novel bot...")
        while True:
            try:
                # Process completed polls
                await novel_tasks.process_completed_polls()
                
                # Wait for next check
                await asyncio.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error processing polls: {str(e)}")
                logger.exception("Detailed error information:")
                await asyncio.sleep(CHECK_INTERVAL)
                
    except Exception as e:
        logger.error(f"Program error: {str(e)}")
        logger.exception("Detailed error information:")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 