"""公告路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user, require_role
from models import core as models
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    course_id: Optional[int] = None
    priority: int = 0


@router.get("/")
def list_announcements(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    q = db.query(models.Announcement)
    if course_id:
        q = q.filter(
            (models.Announcement.course_id == course_id) |
            (models.Announcement.course_id == None)
        )
    return q.order_by(models.Announcement.priority.desc(), models.Announcement.created_at.desc()).all()


@router.post("/", status_code=201)
def create_announcement(
    req: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    a = models.Announcement(**req.model_dump(), author_id=current_user.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{ann_id}")
def delete_announcement(
    ann_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    a = db.query(models.Announcement).filter(models.Announcement.id == ann_id).first()
    if not a:
        raise HTTPException(404, "公告不存在")
    if current_user.role != "admin" and a.author_id != current_user.id:
        raise HTTPException(403, "无权删除")
    db.delete(a)
    db.commit()
    return {"message": "已删除"}
