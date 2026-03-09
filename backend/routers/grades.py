"""成绩路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
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
    q = db.query(models.Grade).options(joinedload(models.Grade.course))
    if current_user.role == "student":
        q = q.filter(models.Grade.student_id == current_user.id)
    elif current_user.role == "teacher":
        # 教师只能查询自己负责课程的成绩（权限收紧，与 assignments 一致）
        my_course_ids = [
            c.id for c in db.query(models.Course)
            .filter(models.Course.teacher_id == current_user.id).all()
        ]
        q = q.filter(models.Grade.course_id.in_(my_course_ids))
    if course_id:
        q = q.filter(models.Grade.course_id == course_id)
    grades = q.all()
    return [
        {
            "id": g.id,
            "course_id": g.course_id,
            "course_name": g.course.name if g.course else "未知",
            "student_id": g.student_id,
            "score": g.score,
            "comment": g.comment,
            "created_at": g.created_at.isoformat(),
        }
        for g in grades
    ]


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
    g = models.Grade(**req.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g
