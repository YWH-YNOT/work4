"""课表路由 - 使用 JWT 认证"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
from models import core as models
from schemas import timetable as timetable_schemas
from services.timetable_parser import TimetableParser
import logging

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

            teacher = db.query(models.User).filter(
                models.User.username == teacher_name,
                models.User.role == "teacher"
            ).first()
            if not teacher:
                # 为教师名创建一个占位账号
                from core.auth import hash_password
                teacher = models.User(
                    username=teacher_name,
                    hashed_password=hash_password("teacher123"),
                    role="teacher"
                )
                db.add(teacher)
                db.commit()
                db.refresh(teacher)

            course = db.query(models.Course).filter(
                models.Course.name == course_name,
                models.Course.teacher_id == teacher.id
            ).first()
            if not course:
                course = models.Course(name=course_name, course_code=course_code, teacher_id=teacher.id)
                db.add(course)
                db.commit()
                db.refresh(course)
                created_courses += 1

            db.query(models.TimetableEntry).filter(
                models.TimetableEntry.student_id == current_user.id,
                models.TimetableEntry.course_id == course.id,
                models.TimetableEntry.day_of_week == item.get("day_of_week"),
                models.TimetableEntry.start_session == item.get("start_session")
            ).delete()

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

        db.commit()
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
    """返回当前用户的课表条目"""
    entries = db.query(models.TimetableEntry).filter(
        models.TimetableEntry.student_id == current_user.id
    ).all()
    result = []
    for e in entries:
        course = db.query(models.Course).filter(models.Course.id == e.course_id).first()
        result.append({
            "id": e.id,
            "course_name": course.name if course else "未知",
            "course_code": course.course_code if course else "",
            "day_of_week": e.day_of_week,
            "start_session": e.start_session,
            "end_session": e.end_session,
            "weeks": e.weeks,
            "location": e.location,
        })
    return result
