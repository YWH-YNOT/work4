"""成绩路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user, require_role
from models import core as models
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class GradeCreate(BaseModel):
    student_id: int
    course_id: int
    score: float
    assignment_id: Optional[int] = None
    comment: Optional[str] = None


@router.get("/")
def get_grades(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(models.Grade)
    if current_user.role == "student":
        q = q.filter(models.Grade.student_id == current_user.id)
    if course_id:
        q = q.filter(models.Grade.course_id == course_id)
    grades = q.all()
    result = []
    for g in grades:
        course = db.query(models.Course).filter(models.Course.id == g.course_id).first()
        result.append({
            "id": g.id,
            "course_id": g.course_id,
            "course_name": course.name if course else "未知",
            "student_id": g.student_id,
            "score": g.score,
            "comment": g.comment,
            "created_at": g.created_at.isoformat(),
        })
    return result


@router.post("/", status_code=200)
def create_or_update_grade(
    req: GradeCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("teacher", "admin"))
):
    """Upsert 成绩：若同一学生+课程已存在则更新，否则新建"""
    existing = db.query(models.Grade).filter(
        models.Grade.student_id == req.student_id,
        models.Grade.course_id == req.course_id,
    ).first()
    if existing:
        existing.score = req.score
        existing.comment = req.comment
        if req.assignment_id is not None:
            existing.assignment_id = req.assignment_id
        db.commit()
        db.refresh(existing)
        return existing
    g = models.Grade(**req.dict())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g
