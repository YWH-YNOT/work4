"""考勤路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.auth import get_current_user, require_role
from models import core as models
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

class SessionCreate(BaseModel):
    course_id: int
    duration_minutes: int = 5
    title: str = "课堂签到"

class CheckinRequest(BaseModel):
    session_id: int

@router.post("/sessions")
def create_session(
    req: SessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    deadline = datetime.utcnow() + timedelta(minutes=req.duration_minutes)
    sess = models.AttendanceSession(
        course_id=req.course_id,
        teacher_id=current_user.id,
        title=req.title,
        deadline=deadline
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess

@router.get("/sessions")
def get_sessions(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(models.AttendanceSession).options(joinedload(models.AttendanceSession.course))
    if course_id:
        q = q.filter(models.AttendanceSession.course_id == course_id)
    if current_user.role == "teacher":
        q = q.filter(models.AttendanceSession.teacher_id == current_user.id)
    
    sessions = q.order_by(models.AttendanceSession.created_at.desc()).all()
    now = datetime.utcnow()
    
    result = []
    for s in sessions:
        is_active = now <= s.deadline
        attendees = db.query(models.Attendance).filter(models.Attendance.session_id == s.id).count()
        result.append({
            "id": s.id,
            "course_id": s.course_id,
            "course_name": s.course.name if s.course else "",
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "deadline": s.deadline.isoformat(),
            "is_active": is_active,
            "attendees": attendees
        })
    return result

@router.post("/checkin")
def checkin(
    req: CheckinRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("student"))
):
    sess = db.query(models.AttendanceSession).filter(models.AttendanceSession.id == req.session_id).first()
    if not sess:
        raise HTTPException(404, "签到任务不存在")
    
    if datetime.utcnow() > sess.deadline:
        raise HTTPException(400, "该签到任务已过期")
        
    existing = db.query(models.Attendance).filter(
        models.Attendance.student_id == current_user.id,
        models.Attendance.session_id == req.session_id
    ).first()
    if existing:
        raise HTTPException(400, "您已完成该次签到")
        
    today = datetime.utcnow().strftime("%Y-%m-%d")
    att = models.Attendance(
        student_id=current_user.id,
        course_id=sess.course_id,
        session_id=sess.id,
        date=today,
        status="present"
    )
    db.add(att)
    db.commit()
    return {"message": "签到成功", "session_id": sess.id}

@router.get("/")
def get_attendance(
    course_id: Optional[int] = None,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(models.Attendance)
    if current_user.role == "student":
        q = q.filter(models.Attendance.student_id == current_user.id)
    elif student_id:
        q = q.filter(models.Attendance.student_id == student_id)
    if course_id:
        q = q.filter(models.Attendance.course_id == course_id)
    return q.order_by(models.Attendance.date.desc()).all()
