"""FastAPI LMS 主应用 - 完整版"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from core.database import engine
from models import core as models
from routers import auth, timetable, chat, courses, admin, assignments, quiz, announcements, attendance, grades, discussions, resources, logs

# Create all database tables
models.Base.metadata.create_all(bind=engine)

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

@app.get("/")
def read_root():
    return {"message": "AI-YWH LMS v2.0", "status": "running"}
