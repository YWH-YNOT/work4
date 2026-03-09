"""FastAPI LMS 主应用 - 完整版"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from core.database import engine
from models import core as models
from routers import auth, timetable, chat, courses, admin, assignments, quiz, announcements, attendance, grades, discussions, resources, logs, posture, face

# Create all database tables
models.Base.metadata.create_all(bind=engine)

# ─── 安全迁移：补充旧 DB 缺失的列（SQLite 不支持 IF NOT EXISTS，用 PRAGMA 判断）───
def _safe_migrate():
    import sqlite3, os
    from core.config import settings
    db_url = str(engine.url)
    if not db_url.startswith("sqlite"):
        return  # 非 SQLite 跳过（生产 PostgreSQL 用 alembic）
    # 从 URL 提取文件路径
    db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "") or "ai_ywh.db"
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # 1. 确保 attendance_sessions 表存在（已由 create_all 处理，此处仅兜底）
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_sessions'")
    if not c.fetchone():
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
    # 2. 补充 attendances.session_id 列
    c.execute("PRAGMA table_info(attendances)")
    att_cols = [r[1] for r in c.fetchall()]
    if "session_id" not in att_cols:
        c.execute("ALTER TABLE attendances ADD COLUMN session_id INTEGER REFERENCES attendance_sessions(id)")
        conn.commit()
        print("✅ 迁移: attendances.session_id 列已添加")
    conn.close()

_safe_migrate()


app = FastAPI(title="AI-YWH LMS", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploaded resources
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(auth.router,          prefix="/api/v1/auth",          tags=["auth"])
app.include_router(courses.router,       prefix="/api/v1/courses",       tags=["courses"])
app.include_router(timetable.router,     prefix="/api/v1/timetable",     tags=["timetable"])
app.include_router(chat.router,          prefix="/api/v1/chat",          tags=["chat"])
app.include_router(resources.router,     prefix="/api/v1/resources",     tags=["resources"])
app.include_router(assignments.router,   prefix="/api/v1/assignments",   tags=["assignments"])
app.include_router(quiz.router,          prefix="/api/v1/quiz",          tags=["quiz"])
app.include_router(announcements.router, prefix="/api/v1/announcements", tags=["announcements"])
app.include_router(attendance.router,    prefix="/api/v1/attendance",    tags=["attendance"])
app.include_router(grades.router,        prefix="/api/v1/grades",        tags=["grades"])
app.include_router(discussions.router,   prefix="/api/v1/discussions",   tags=["discussions"])
app.include_router(logs.router,          prefix="/api/v1/logs",          tags=["logs"])
app.include_router(admin.router,         prefix="/api/v1/admin",         tags=["admin"])
app.include_router(posture.router,       prefix="/api/v1/posture",       tags=["posture"])
app.include_router(face.router,          prefix="/api/v1/face",          tags=["face"])

@app.get("/")
def read_root():
    return {"message": "AI-YWH LMS v2.0", "status": "running"}
