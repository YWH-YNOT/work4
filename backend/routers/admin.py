"""管理员路由：用户管理"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import require_role
from models import core as models
from typing import List
from pydantic import BaseModel

router = APIRouter()


class UserAdminOut(BaseModel):
    id: int
    username: str
    email: str | None
    full_name: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserAdminOut])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    return db.query(models.User).all()


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}


@router.patch("/users/{user_id}/toggle")
def toggle_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = not user.is_active
    db.commit()
    return {"message": "状态已切换", "is_active": user.is_active}


@router.get("/stats")
def system_stats(
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    return {
        "total_users": db.query(models.User).count(),
        "students": db.query(models.User).filter(models.User.role == "student").count(),
        "teachers": db.query(models.User).filter(models.User.role == "teacher").count(),
        "total_courses": db.query(models.Course).count(),
        "total_assignments": db.query(models.Assignment).count(),
        "total_chat_logs": db.query(models.ChatLog).count(),
    }
