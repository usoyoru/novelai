from app.database import SessionLocal
from app.models.novel import Novel, Chapter, PlotOption, Vote

def check_database():
    """Check database status and display summary"""
    try:
        # Create database session
        db = SessionLocal()
        
        # Get all novels
        novels = db.query(Novel).all()
        print(f"\nFound {len(novels)} novels:")
        
        for novel in novels:
            print(f"\nNovel: {novel.title}")
            print(f"ID: {novel.id}")
            print(f"Genre: {novel.genre}")
            print(f"Current Chapter: {novel.current_chapter}")
            print(f"Created at: {novel.created_at}")
            
            # Get chapters
            chapters = db.query(Chapter).filter(Chapter.novel_id == novel.id).all()
            print(f"Total Chapters: {len(chapters)}")
            
            # Get plot options
            plot_options = db.query(PlotOption).filter(PlotOption.novel_id == novel.id).all()
            print(f"Total Plot Options: {len(plot_options)}")
            
            # Get votes
            votes = db.query(Vote).join(PlotOption).filter(PlotOption.novel_id == novel.id).all()
            print(f"Total Votes: {len(votes)}")
            
            print("\nLatest Plot Options:")
            latest_options = db.query(PlotOption).filter(
                PlotOption.novel_id == novel.id,
                PlotOption.chapter_number == novel.current_chapter
            ).all()
            
            for option in latest_options:
                print(f"Option {option.option_id}: {option.title} (Votes: {option.votes_count})")
        
    except Exception as e:
        print(f"Error checking database: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database() 