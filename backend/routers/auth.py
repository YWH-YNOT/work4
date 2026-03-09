"""认证路由：注册/登录/获取当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
import glob
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


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None


@router.put("/profile", response_model=UserOut)
def update_profile(
    req: ProfileUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 只更新提供的且非空的值
    if req.full_name is not None:
        current_user.full_name = req.full_name.strip() or None
    if req.password:
        current_user.hashed_password = hash_password(req.password)
        
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/upload-face")
async def upload_face(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="仅学生可以注册人脸")

    # 必须先设置真实姓名，否则文件名中的 name 部分会缺失
    if not current_user.full_name:
        raise HTTPException(
            status_code=400,
            detail="请先在个人中心设置真实姓名（用于人脸识别匹配），再上传照片"
        )

    ext = (file.filename or "").split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png 格式图片")

    name_for_file = current_user.full_name
    face_db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "face_db")
    os.makedirs(face_db_dir, exist_ok=True)

    # 删除该学号以前可能存在的旧照片
    old_files = glob.glob(os.path.join(face_db_dir, f"{current_user.username}_*.*"))
    for old_f in old_files:
        try:
            os.remove(old_f)
        except Exception:
            pass

    # 保存新文件: username_fullname.ext
    new_filename = f"{current_user.username}_{name_for_file}.{ext}"
    new_path = os.path.join(face_db_dir, new_filename)

    contents = await file.read()
    with open(new_path, "wb") as fp:
        fp.write(contents)

    # 尝试热更新人脸库
    try:
        from routers.posture import _load_face_hists
        _load_face_hists()
    except Exception as e:
        print(f"Warning: Failed to reload face hists: {e}")

    return {"msg": "人脸注册成功", "filename": new_filename}
