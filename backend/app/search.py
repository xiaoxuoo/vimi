import sqlite3
import os

def view_all_users():
    # 确定 dev.db 路径
    db_path = os.path.join(os.path.dirname(__file__), 'dev.db')

    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，请先确认项目运行过并生成数据库！")
        return

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 输出所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print("数据库中的表：")
    for t in tables:
        print("-", t)

    # 查看 users 表的数据
    print("\n--- 用户信息 ---")
    if "users" not in tables:
        print("当前数据库中没有 'users' 表，请确认是否已初始化数据库。")
    else:
        cursor.execute("SELECT id, username, email, role, created_at FROM users;")
        rows = cursor.fetchall()
        if not rows:
            print("users 表存在，但没有任何用户数据。")
        else:
            for row in rows:
                print(f"ID: {row[0]}, 用户名: {row[1]}, 邮箱: {row[2]}, 角色: {row[3]}, 注册时间: {row[4]}")

    conn.close()

if __name__ == "__main__":
    view_all_users()
