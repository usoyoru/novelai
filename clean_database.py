from app import app, db, Story, Option, Vote

def clean_database():
    """Clean all data from the database"""
    with app.app_context():
        print("\nCurrent database status:")
        print("-" * 40)
        stories = Story.query.all()
        options = Option.query.all()
        votes = Vote.query.all()
        print(f"Stories: {len(stories)}")
        print(f"Options: {len(options)}")
        print(f"Votes: {len(votes)}")
        
        # List all stories
        if stories:
            print("\nExisting stories:")
            for story in stories:
                print(f"- {story.title} (Chapter {story.current_chapter})")
        
        # Ask for confirmation
        confirm = input("\nAre you sure you want to clean the database? This action cannot be undone! (yes/no): ")
        
        if confirm.lower() == 'yes':
            try:
                # Delete all votes first (due to foreign key constraints)
                Vote.query.delete()
                print("Deleted all votes")
                
                # Delete all options
                Option.query.delete()
                print("Deleted all options")
                
                # Delete all stories
                Story.query.delete()
                print("Deleted all stories")
                
                # Commit the changes
                db.session.commit()
                print("\nDatabase cleaned successfully!")
                
            except Exception as e:
                print(f"\nError cleaning database: {e}")
                db.session.rollback()
                print("Operation rolled back")
        else:
            print("\nOperation cancelled")

if __name__ == "__main__":
    print("AI Interactive Novel - Database Cleaner")
    print("=" * 40)
    print("\nWARNING: This script will delete all data from the database!")
    clean_database() 