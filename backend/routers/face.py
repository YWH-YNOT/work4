"""
人脸注册与识别路由
- POST /enroll      上传照片注册学生人脸
- GET  /students    查询已注册学生
- DELETE /students/{student_id}  删除注册
- POST /identify    识别一张人脸照片（返回最匹配学生）
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os, base64, json, shutil
from pathlib import Path
from typing import Optional

router = APIRouter()

FACE_DB_DIR = Path(__file__).parent.parent / "face_db"
FACE_DB_DIR.mkdir(exist_ok=True)

# 已注册学生元数据（内存缓存）
# 格式: {student_id: {"name": ..., "photo_path": ...}}
_face_registry: dict = {}


def _load_registry():
    """从 face_db 目录扫描加载注册信息（文件名格式: {学号}_{姓名}.jpg）"""
    global _face_registry
    _face_registry = {}
    for f in FACE_DB_DIR.glob("*.jpg"):
        parts = f.stem.split("_", 1)
        if len(parts) == 2:
            student_id, name = parts
            _face_registry[student_id] = {
                "student_id": student_id,
                "name": name,
                "photo_path": str(f),
            }
    return _face_registry


# 启动时加载
_load_registry()


@router.post("/enroll")
async def enroll_face(
    student_id: str = Form(...),
    name:       str = Form(...),
    photo:      UploadFile = File(...),
):
    """注册学生人脸（上传照片）"""
    ext = Path(photo.filename or "face.jpg").suffix or ".jpg"
    save_path = FACE_DB_DIR / f"{student_id}_{name}{ext}"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    _load_registry()
    return {"ok": True, "student_id": student_id, "name": name}


@router.post("/enroll-base64")
async def enroll_face_base64(body: dict):
    """注册学生人脸（base64 照片）"""
    student_id = body.get("student_id", "")
    name       = body.get("name", "")
    photo_b64  = body.get("photo_b64", "")
    if not all([student_id, name, photo_b64]):
        raise HTTPException(400, "缺少参数")
    img_bytes = base64.b64decode(photo_b64)
    save_path = FACE_DB_DIR / f"{student_id}_{name}.jpg"
    save_path.write_bytes(img_bytes)
    _load_registry()
    return {"ok": True, "student_id": student_id, "name": name}


@router.get("/students")
def list_students():
    """列出已注册的学生人脸"""
    _load_registry()
    return list(_face_registry.values())


@router.delete("/students/{student_id}")
def delete_student(student_id: str):
    """删除已注册学生的人脸"""
    if student_id not in _face_registry:
        raise HTTPException(404, "未找到")
    info = _face_registry.pop(student_id)
    Path(info["photo_path"]).unlink(missing_ok=True)
    return {"ok": True}


@router.post("/identify")
async def identify_face(body: dict):
    """
    识别人脸（接收 base64 JPEG，返回最匹配的学生）。
    使用 deepface 做余弦相似度比对。
    """
    face_b64 = body.get("face_b64", "")
    if not face_b64:
        raise HTTPException(400, "缺少 face_b64")

    try:
        from deepface import DeepFace
    except ImportError:
        raise HTTPException(500, "deepface 未安装，请运行: pip install deepface tf-keras")

    import tempfile, numpy as np

    # 把输入图写到临时文件
    img_data = base64.b64decode(face_b64)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        tf.write(img_data)
        tmp_path = tf.name

    best_match = None
    best_dist  = 999.0
    _load_registry()

    try:
        for sid, info in _face_registry.items():
            try:
                result = DeepFace.verify(
                    img1_path=tmp_path,
                    img2_path=info["photo_path"],
                    model_name="Facenet",
                    enforce_detection=False,
                )
                dist = result.get("distance", 999)
                if dist < best_dist:
                    best_dist  = dist
                    best_match = {**info, "distance": round(dist, 3)}
            except Exception:
                continue
    finally:
        os.unlink(tmp_path)

    if best_match and best_dist < 0.6:   # 阈值：越小越严格
        return {"matched": True, **best_match}
    return {"matched": False, "distance": round(best_dist, 3)}
