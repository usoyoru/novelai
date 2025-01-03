import sqlite3
import json
from datetime import datetime

def print_table_contents(cursor, table_name):
    print(f"\n=== {table_name} 表内容 ===")
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # 获取列名
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    
    # 打印每一行
    for row in rows:
        print("\n---")
        for col_name, value in zip(columns, row):
            if isinstance(value, str) and len(value) > 100:
                print(f"{col_name}: {value[:100]}...")
            else:
                print(f"{col_name}: {value}")

def main():
    conn = sqlite3.connect('novel_bot.db')
    cursor = conn.cursor()
    
    # 查看所有表的内容
    tables = ['novels', 'chapters', 'plot_options', 'votes']
    for table in tables:
        try:
            print_table_contents(cursor, table)
        except sqlite3.OperationalError as e:
            print(f"\n表 {table} 不存在或无法访问: {str(e)}")
    
    conn.close()

if __name__ == "__main__":
    main() 