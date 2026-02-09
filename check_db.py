import sqlite3

# 连接数据库
conn = sqlite3.connect('data/reInput.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("数据库表:")
for table in tables:
    print(f"  - {table[0]}")

# 查看用户表数据
print("\n用户表数据:")
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
for user in users:
    print(f"  用户ID: {user[0]}, 显示名称: {user[1]}")

conn.close()
print("\n数据库检查完成！")