"""资源文件路由"""
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user, require_role
from models import core as models

router = APIRouter()
UPLOAD_DIR = "uploads"
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@router.get("/")
def list_resources(
    course_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    resources = db.query(models.Resource).filter(models.Resource.course_id == course_id).all()
    return [{
        "id": r.id, "filename": r.filename,
        "file_size": r.file_size,
        "uploader_id": r.uploader_id,
        "created_at": r.created_at.isoformat(),
    } for r in resources]


@router.post("/upload")
async def upload_resource(
    course_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "文件不能超过 10MB")

    safe_name = f"{current_user.id}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, safe_name)
    with open(filepath, "wb") as f:
        f.write(content)

    resource = models.Resource(
        course_id=course_id,
        uploader_id=current_user.id,
        filename=file.filename,
        filepath=filepath,
        file_size=len(content),
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return {"message": "上传成功", "id": resource.id, "filename": resource.filename}


@router.get("/{resource_id}/download")
def download_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    r = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not r or not os.path.exists(r.filepath):
        raise HTTPException(404, "文件不存在")
    return FileResponse(r.filepath, filename=r.filename)


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    r = db.query(models.Resource).filter(models.Resource.id == resource_id).first()
    if not r:
        raise HTTPException(404, "资源不存在")
    if current_user.role != "admin" and r.uploader_id != current_user.id:
        raise HTTPException(403, "无权删除")
    if os.path.exists(r.filepath):
        os.remove(r.filepath)
    db.delete(r)
    db.commit()
    return {"message": "已删除"}
