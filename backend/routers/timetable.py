"""课表路由 - 使用 JWT 认证"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.auth import get_current_user
from models import core as models
from schemas import timetable as timetable_schemas
from services.timetable_parser import TimetableParser
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/import", response_model=timetable_schemas.TimetableImportResponse)
async def import_timetable(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    image_bytes = await file.read()
    content_type = file.content_type or "image/jpeg"
    parser = TimetableParser()
    parsed_data = parser.parse_image(image_bytes, content_type)

    if not parsed_data:
        raise HTTPException(status_code=422, detail="Vision 模型未能识别任何课程，请确认上传的是课表截图")

    created_courses = 0
    created_entries = 0

    try:
        for item in parsed_data:
            course_name = item.get("course_name")
            course_code = item.get("course_code", "")
            teacher_name = item.get("teacher_name", "Unknown Teacher")

            if not course_name:
                continue

            # 先按 full_name 查真实教师，再按 username 查，都没有才创建占位账号
            teacher = db.query(models.User).filter(
                models.User.full_name == teacher_name,
                models.User.role == "teacher"
            ).first()
            if not teacher:
                teacher = db.query(models.User).filter(
                    models.User.username == teacher_name,
                    models.User.role == "teacher"
                ).first()
            if not teacher:
                # 创建占位账号，密码使用随机 UUID 保证安全
                from core.auth import hash_password
                placeholder_username = f"teacher_{uuid.uuid4().hex[:8]}"
                teacher = models.User(
                    username=placeholder_username,
                    full_name=teacher_name,
                    hashed_password=hash_password(uuid.uuid4().hex),
                    role="teacher"
                )
                db.add(teacher)
                db.flush()  # 获取 id 但不 commit，由最外层统一提交

            course = db.query(models.Course).filter(
                models.Course.name == course_name,
                models.Course.teacher_id == teacher.id
            ).first()
            if not course:
                course = models.Course(name=course_name, course_code=course_code, teacher_id=teacher.id)
                db.add(course)
                db.flush()  # 获取 id
                created_courses += 1

            db.query(models.TimetableEntry).filter(
                models.TimetableEntry.student_id == current_user.id,
                models.TimetableEntry.course_id == course.id,
                models.TimetableEntry.day_of_week == item.get("day_of_week"),
                models.TimetableEntry.start_session == item.get("start_session")
            ).delete(synchronize_session=False)

            entry = models.TimetableEntry(
                student_id=current_user.id,
                course_id=course.id,
                day_of_week=item.get("day_of_week"),
                start_session=item.get("start_session"),
                end_session=item.get("end_session"),
                weeks=item.get("weeks"),
                location=item.get("location")
            )
            db.add(entry)
            created_entries += 1

        db.commit()  # 所有操作统一提交
    except Exception as e:
        db.rollback()
        logger.error(f"DB error during timetable import: {e}")
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")

    return timetable_schemas.TimetableImportResponse(
        message="课表解析并导入成功",
        courses_imported=created_courses,
        timetable_entries_created=created_entries
    )


@router.get("/")
def get_timetable(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """返回当前用户的课表条目（joinedload 消除 N+1 查询）"""
    entries = (
        db.query(models.TimetableEntry)
        .options(joinedload(models.TimetableEntry.course))
        .filter(models.TimetableEntry.student_id == current_user.id)
        .all()
    )
    return [
        {
            "id": e.id,
            "course_name": e.course.name if e.course else "未知",
            "course_code": e.course.course_code if e.course else "",
            "day_of_week": e.day_of_week,
            "start_session": e.start_session,
            "end_session": e.end_session,
            "weeks": e.weeks,
            "location": e.location,
        }
        for e in entries
    ]
