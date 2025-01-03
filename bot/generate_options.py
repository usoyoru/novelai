import asyncio
from app.database import SessionLocal
from app.models.novel import Novel, Chapter
from app.services.ai_service import AIService
from app.tasks.novel_tasks import NovelTasks

async def generate_options():
    """Generate voting options for the latest chapter"""
    try:
        # Create database session
        db = SessionLocal()
        
        # Get latest novel
        novel = db.query(Novel).order_by(Novel.created_at.desc()).first()
        if not novel:
            print("No novels found in database")
            return
            
        # Create service instances
        ai_service = AIService()
        novel_tasks = NovelTasks(db, ai_service)
        
        # Generate options for current chapter
        await novel_tasks.generate_chapter_with_options(novel.id, novel.current_chapter)
        print("Successfully generated voting options")
        
    except Exception as e:
        print(f"Error generating options: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(generate_options()) 