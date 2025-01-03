import os
import sqlite3
from datetime import datetime, timedelta

def clean_database():
    """Clean up old records from the database"""
    try:
        # Get database path
        db_path = os.path.join(os.path.dirname(__file__), 'novel_bot.db')
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current time
        current_time = datetime.now()
        
        # Calculate cutoff time (30 days ago)
        cutoff_time = current_time - timedelta(days=30)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Delete old novels and related records
        cursor.execute("""
            DELETE FROM votes 
            WHERE plot_option_id IN (
                SELECT id FROM plot_options 
                WHERE novel_id IN (
                    SELECT id FROM novels 
                    WHERE created_at < ?
                )
            )
        """, (cutoff_str,))
        
        cursor.execute("""
            DELETE FROM plot_options 
            WHERE novel_id IN (
                SELECT id FROM novels 
                WHERE created_at < ?
            )
        """, (cutoff_str,))
        
        cursor.execute("""
            DELETE FROM chapters 
            WHERE novel_id IN (
                SELECT id FROM novels 
                WHERE created_at < ?
            )
        """, (cutoff_str,))
        
        cursor.execute("DELETE FROM novels WHERE created_at < ?", (cutoff_str,))
        
        # Commit changes
        conn.commit()
        print("Database cleanup completed")
        
    except Exception as e:
        print(f"Error during database cleanup: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    clean_database() 