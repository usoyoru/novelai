import os
import sys
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bot.app.models.novel import Novel, Chapter, PlotOption, Vote
import subprocess
import signal

def get_database_url():
    """Get database URL"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        return DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return "sqlite:///./novel_bot.db"

def clean_database():
    """Clean up database"""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get all novels
        novels = session.query(Novel).all()
        
        if not novels:
            print("No novels found in database")
            return
            
        print(f"Found {len(novels)} novels:")
        for novel in novels:
            print(f"- {novel.title} (ID: {novel.id})")
            
        confirm = input("Are you sure you want to delete all novel data? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return
            
        # Delete all data
        session.query(Vote).delete()
        session.query(PlotOption).delete()
        session.query(Chapter).delete()
        session.query(Novel).delete()
        
        session.commit()
        print("All data has been cleaned up")
        
    except Exception as e:
        print(f"Error cleaning database: {str(e)}")
        session.rollback()
    finally:
        session.close()

def start_bot():
    """Start the bot"""
    try:
        print("Starting bot...")
        process = subprocess.Popen([sys.executable, "bot/main.py"])
        print(f"Bot started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"Error starting bot: {str(e)}")
        return None

def stop_bot(process):
    """Stop the bot"""
    if process:
        try:
            print(f"Stopping bot (PID: {process.pid})...")
            os.kill(process.pid, signal.SIGTERM)
            process.wait()
            print("Bot stopped")
        except Exception as e:
            print(f"Error stopping bot: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Novel Bot Management Tool")
    parser.add_argument('action', choices=['clean', 'start', 'stop'], help='Action to perform')
    
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
        print("Please use Ctrl+C to stop the bot")

if __name__ == "__main__":
    main() 