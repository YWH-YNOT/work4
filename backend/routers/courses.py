"""课程路由 - 使用 JWT 认证"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.auth import get_current_user, require_role
from models import core as models
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class CourseCreate(BaseModel):
    name: str
    course_code: Optional[str] = None
    description: Optional[str] = None


@router.get("/my")
def get_my_courses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取当前学生的课程（通过课表），或当前教师创建的课程"""
    if current_user.role == "teacher":
        courses = db.query(models.Course).filter(models.Course.teacher_id == current_user.id).all()
        return [{"id": c.id, "name": c.name, "course_code": c.course_code or "", "description": c.description} for c in courses]
    
    # 学生：通过 TimetableEntry
    entries = db.query(models.TimetableEntry).filter(models.TimetableEntry.student_id == current_user.id).all()
    student_course_ids = {e.course_id for e in entries}
    if not student_course_ids:
        return []
    courses = (
        db.query(models.Course)
        .filter(models.Course.id.in_(student_course_ids))
        .options(joinedload(models.Course.teacher))
        .all()
    )
    seen, unique = set(), []
    for c in courses:
        if c.name not in seen:
            seen.add(c.name)
            unique.append({
                "id": c.id,
                "name": c.name,
                "course_code": c.course_code or "",
                "teacher_name": c.teacher.username if c.teacher else "未知",
                "description": c.description,
            })
    return unique


@router.get("/")
def list_all_courses(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(models.Course).options(joinedload(models.Course.teacher)).all()


@router.post("/", status_code=201)
def create_course(
    req: CourseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    c = models.Course(**req.dict(), teacher_id=current_user.id)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "课程不存在")
    if current_user.role != "admin" and c.teacher_id != current_user.id:
        raise HTTPException(403, "无权删除")
    db.delete(c)
    db.commit()
    return {"message": "已删除"}
