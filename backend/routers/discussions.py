"""讨论区路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from core.database import get_db
from core.auth import get_current_user
from models import core as models
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class DiscussionCreate(BaseModel):
    course_id: int
    title: str
    content: str


class CommentCreate(BaseModel):
    content: str


@router.get("/")
def list_discussions(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    # 使用子查询统计回复数，避免 N+1 查询
    comment_count = (
        db.query(models.Comment.discussion_id, func.count(models.Comment.id).label("cnt"))
        .group_by(models.Comment.discussion_id)
        .subquery()
    )
    q = (
        db.query(models.Discussion, comment_count.c.cnt)
        .options(joinedload(models.Discussion.author))
        .outerjoin(comment_count, models.Discussion.id == comment_count.c.discussion_id)
    )
    if course_id:
        q = q.filter(models.Discussion.course_id == course_id)
    rows = q.order_by(models.Discussion.created_at.desc()).all()
    return [{
        "id": d.id, "course_id": d.course_id, "title": d.title,
        "content": d.content, "views": d.views,
        "author": d.author.username if d.author else "未知",
        "created_at": d.created_at.isoformat(),
        "reply_count": cnt or 0,
    } for d, cnt in rows]


@router.post("/", status_code=201)
def create_discussion(
    req: DiscussionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    d = models.Discussion(**req.dict(), author_id=current_user.id)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.get("/{discussion_id}")
def get_discussion(
    discussion_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    d = db.query(models.Discussion).options(
        joinedload(models.Discussion.comments).joinedload(models.Comment.author)
    ).filter(models.Discussion.id == discussion_id).first()
    if not d:
        raise HTTPException(404, "帖子不存在")
    d.views += 1
    db.commit()
    return {
        "id": d.id, "title": d.title, "content": d.content,
        "views": d.views, "created_at": d.created_at.isoformat(),
        "comments": [{
            "id": c.id, "content": c.content,
            "author": c.author.username if c.author else "未知",
            "created_at": c.created_at.isoformat()
        } for c in d.comments]
    }


@router.post("/{discussion_id}/comments")
def add_comment(
    discussion_id: int,
    req: CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first():
        raise HTTPException(404, "帖子不存在")
    c = models.Comment(discussion_id=discussion_id, author_id=current_user.id, content=req.content)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
