"""对话日志路由（教师查看）"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.auth import require_role
from models import core as models
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("/")
def get_logs(
    course_id: Optional[int] = None,
    student_id: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _=Depends(require_role("teacher", "admin"))
):
    q = db.query(models.ChatLog).options(
        joinedload(models.ChatLog.user),
        joinedload(models.ChatLog.course)
    )
    if course_id:
        q = q.filter(models.ChatLog.course_id == course_id)
    if student_id:
        q = q.filter(models.ChatLog.user_id == student_id)
    if keyword:
        q = q.filter(models.ChatLog.content.ilike(f"%{keyword}%"))

    total = q.count()
    logs = q.order_by(models.ChatLog.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [{
            "id": l.id,
            "user": l.user.username if l.user else "未知",
            "course": l.course.name if l.course else None,
            "role": l.role,
            "content": l.content[:200],
            "conversation_id": l.conversation_id,
            "created_at": l.created_at.isoformat(),
        } for l in logs]
    }
