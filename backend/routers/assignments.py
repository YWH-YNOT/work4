"""作业管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user, require_role
from models import core as models
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    type: str = "homework"
    due_date: Optional[datetime] = None


class SubmissionCreate(BaseModel):
    content: Optional[str] = None


class GradeSubmission(BaseModel):
    score: float
    feedback: Optional[str] = None


@router.get("/")
def list_assignments(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(models.Assignment)
    if course_id:
        q = q.filter(models.Assignment.course_id == course_id)
    # 教师只看自己课程的作业
    if current_user.role == "teacher":
        my_course_ids = [
            c.id for c in db.query(models.Course).filter(models.Course.teacher_id == current_user.id).all()
        ]
        q = q.filter(models.Assignment.course_id.in_(my_course_ids))
    assignments = q.order_by(models.Assignment.created_at.desc()).all()
    result = []
    for a in assignments:
        sub = None
        submissions_count = None
        if current_user.role == "student":
            sub = db.query(models.Submission).filter(
                models.Submission.assignment_id == a.id,
                models.Submission.student_id == current_user.id
            ).first()
        elif current_user.role in ("teacher", "admin"):
            submissions_count = db.query(models.Submission).filter(
                models.Submission.assignment_id == a.id
            ).count()
        result.append({
            "id": a.id, "course_id": a.course_id, "title": a.title,
            "description": a.description, "type": a.type,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "created_at": a.created_at.isoformat(),
            "submitted": sub is not None,
            "score": sub.score if sub else None,
            "submissions_count": submissions_count,
        })
    return result


@router.post("/")
def create_assignment(
    req: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    a = models.Assignment(**req.dict())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.post("/{assignment_id}/submit")
def submit_assignment(
    assignment_id: int,
    req: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("student"))
):
    if not db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first():
        raise HTTPException(404, "作业不存在")
    existing = db.query(models.Submission).filter(
        models.Submission.assignment_id == assignment_id,
        models.Submission.student_id == current_user.id
    ).first()
    if existing:
        existing.content = req.content
        existing.submitted_at = datetime.utcnow()
        db.commit()
        return existing
    sub = models.Submission(assignment_id=assignment_id, student_id=current_user.id, content=req.content)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/{assignment_id}/submissions")
def list_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("teacher", "admin"))
):
    return db.query(models.Submission).filter(models.Submission.assignment_id == assignment_id).all()


@router.patch("/submissions/{submission_id}/grade")
def grade_submission(
    submission_id: int,
    req: GradeSubmission,
    db: Session = Depends(get_db),
    _=Depends(require_role("teacher", "admin"))
):
    sub = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(404, "提交不存在")
    sub.score = req.score
    sub.feedback = req.feedback
    db.commit()
    return {"message": "批改成功"}
