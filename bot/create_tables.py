from app.database import init_db

def create_tables():
    """Create all database tables"""
    try:
        init_db()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {str(e)}")

if __name__ == "__main__":
    create_tables() 