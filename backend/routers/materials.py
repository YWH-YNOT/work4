import os
import shutil
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import require_role
from models import core as models
from services.document_processor import DocumentProcessor
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads/course_materials"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_course_material(
    course_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    """
    Upload a course material (PDF, TXT), save it locally,
    and process it into the RAG Vector DB (ChromaDB) for AI ingestion.
    仅限教师上传自己课程的材料（管理员可上传任意课程）。
    """
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    # 权限校验：教师只能上传自己课程的材料
    if current_user.role == "teacher" and course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权向该课程上传材料")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".pdf", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail="仅支持 PDF、TXT、MD 格式")

    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        processor = DocumentProcessor()
        metadata = {
            "course_id": course_id,
            "filename": file.filename,
            "source": unique_filename
        }
        num_chunks = processor.process_file(file_path, metadata)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

    return {
        "message": "文件已成功上传并写入向量数据库",
        "filename": file.filename,
        "chunks_indexed": num_chunks
    }

