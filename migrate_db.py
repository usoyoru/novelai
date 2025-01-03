from bot.app.database import migrate_votes_to_wallet

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_votes_to_wallet()
    print("Database migration completed") 