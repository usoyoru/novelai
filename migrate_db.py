from bot.app.database import migrate_votes_to_wallet

if __name__ == "__main__":
    print("开始数据库迁移...")
    migrate_votes_to_wallet()
    print("数据库迁移完成") 