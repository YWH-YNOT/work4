from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from core.database import get_db
from core.auth import get_current_user, require_role
from models import core as models
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
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
    deadline = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=req.duration_minutes)
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
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # 一次子查询批量获取签到人数，消除 N+1
    session_ids = [s.id for s in sessions]
    attendee_map: dict = {}
    if session_ids:
        rows = (
            db.query(models.Attendance.session_id, func.count(models.Attendance.id).label("cnt"))
            .filter(models.Attendance.session_id.in_(session_ids))
            .group_by(models.Attendance.session_id)
            .all()
        )
        attendee_map = {r.session_id: r.cnt for r in rows}
    
    result = []
    for s in sessions:
        is_active = now <= s.deadline
        result.append({
            "id": s.id,
            "course_id": s.course_id,
            "course_name": s.course.name if s.course else "",
            "title": s.title,
            "created_at": s.created_at.isoformat(),
            "deadline": s.deadline.isoformat(),
            "is_active": is_active,
            "attendees": attendee_map.get(s.id, 0)
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
    
    if datetime.now(timezone.utc).replace(tzinfo=None) > sess.deadline:
        raise HTTPException(400, "该签到任务已过期")
        
    existing = db.query(models.Attendance).filter(
        models.Attendance.student_id == current_user.id,
        models.Attendance.session_id == req.session_id
    ).first()
    if existing:
        raise HTTPException(400, "您已完成该次签到")
        
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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
        # 学生只能查自己的签到
        q = q.filter(models.Attendance.student_id == current_user.id)
    elif current_user.role == "teacher":
        # 教师只能查看自己课程的签到记录（权限收紧，防止数据泄漏）
        my_course_ids = [
            c.id for c in db.query(models.Course)
            .filter(models.Course.teacher_id == current_user.id).all()
        ]
        q = q.filter(models.Attendance.course_id.in_(my_course_ids))
        if student_id:
            q = q.filter(models.Attendance.student_id == student_id)
    else:
        # admin 无限制，可按 student_id 额外过滤
        if student_id:
            q = q.filter(models.Attendance.student_id == student_id)
    if course_id:
        q = q.filter(models.Attendance.course_id == course_id)
    return q.order_by(models.Attendance.date.desc()).all()
