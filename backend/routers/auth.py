"""认证路由：注册/登录/获取当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from core.database import get_db
from core.auth import hash_password, verify_password, create_access_token, get_current_user
from models import core as models

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "student"   # student | teacher | admin


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    user_id: int


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserOut, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # 空字符串转 None，防止 unique 约束炸裂（SQLite 中 "" != NULL）
    if req.email is not None and not req.email.strip():
        req.email = None
    if req.full_name is not None and not req.full_name.strip():
        req.full_name = None

    if db.query(models.User).filter(models.User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if req.email and db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    if req.role not in ("student", "teacher", "admin"):
        raise HTTPException(status_code=400, detail="角色无效，必须为 student/teacher/admin")

    user = models.User(
        username=req.username,
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        role=user.role,
        username=user.username,
        user_id=user.id,
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user=Depends(get_current_user)):
    return current_user
