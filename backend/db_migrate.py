"""
数据库 Schema 迁移脚本
补充 attendances.session_id 列（SQLite ALTER TABLE ADD COLUMN）
确保 attendance_sessions 表存在
"""
import sqlite3, sys

DB_PATH = "ai_ywh.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 查看现有表
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("当前表:", tables)

# 1. 确保 attendance_sessions 表存在
if "attendance_sessions" not in tables:
    print("创建 attendance_sessions 表...")
    c.execute("""
        CREATE TABLE attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER REFERENCES courses(id),
            teacher_id INTEGER REFERENCES users(id),
            title VARCHAR DEFAULT '课堂签到',
            deadline DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("✅ attendance_sessions 表已创建")
else:
    print("✅ attendance_sessions 表已存在")

# 2. 查看 attendances 表列
c.execute("PRAGMA table_info(attendances)")
att_cols = [r[1] for r in c.fetchall()]
print("attendances 列:", att_cols)

# 3. 补充 session_id 列（若不存在）
if "session_id" not in att_cols:
    print("添加 attendances.session_id 列...")
    c.execute("ALTER TABLE attendances ADD COLUMN session_id INTEGER REFERENCES attendance_sessions(id)")
    conn.commit()
    print("✅ session_id 列已添加")
else:
    print("✅ session_id 列已存在")

conn.close()
print("迁移完成！")
