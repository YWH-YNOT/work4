"""测验路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user, require_role
from models import core as models
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

router = APIRouter()


class QuizCreate(BaseModel):
    course_id: int
    title: str
    time_limit: Optional[int] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class QuestionCreate(BaseModel):
    question: str
    options: List[str]
    correct_option: int


class AttemptCreate(BaseModel):
    answers: dict   # {str(question_id): int(selected)}


@router.get("/")
def list_quizzes(course_id: Optional[int] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    q = db.query(models.Quiz)
    if course_id:
        q = q.filter(models.Quiz.course_id == course_id)
    quizzes = q.order_by(models.Quiz.created_at.desc()).all()

    # 学生：批量查询已作答记录，避免 N+1
    attempt_map: dict = {}
    if current_user.role == "student":
        quiz_ids = [qz.id for qz in quizzes]
        if quiz_ids:
            attempts = db.query(models.QuizAttempt).filter(
                models.QuizAttempt.student_id == current_user.id,
                models.QuizAttempt.quiz_id.in_(quiz_ids)
            ).all()
            attempt_map = {a.quiz_id: a for a in attempts}

    return [{
        "id": qz.id, "title": qz.title, "course_id": qz.course_id,
        "time_limit": qz.time_limit,
        "start_at": qz.start_at.isoformat() if qz.start_at else None,
        "end_at": qz.end_at.isoformat() if qz.end_at else None,
        "question_count": len(qz.questions),
        "attempted": qz.id in attempt_map,
        "my_score": attempt_map[qz.id].score if qz.id in attempt_map else None,
    } for qz in quizzes]


@router.post("/")
def create_quiz(req: QuizCreate, db: Session = Depends(get_db), _=Depends(require_role("teacher", "admin"))):
    qz = models.Quiz(**req.model_dump())
    db.add(qz)
    db.commit()
    db.refresh(qz)
    return qz


@router.post("/{quiz_id}/questions")
def add_question(quiz_id: int, req: QuestionCreate, db: Session = Depends(get_db), _=Depends(require_role("teacher", "admin"))):
    q = models.QuizQuestion(quiz_id=quiz_id, **req.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.get("/{quiz_id}")
def get_quiz(quiz_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    qz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not qz:
        raise HTTPException(404, "测验不存在")
    questions = []
    for q in qz.questions:
        item = {"id": q.id, "question": q.question, "options": q.options}
        if current_user.role in ("teacher", "admin"):
            item["correct_option"] = q.correct_option
        questions.append(item)
    return {"id": qz.id, "title": qz.title, "time_limit": qz.time_limit, "questions": questions}


@router.post("/{quiz_id}/submit")
def submit_quiz(quiz_id: int, req: AttemptCreate, db: Session = Depends(get_db), current_user=Depends(require_role("student"))):
    qz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not qz:
        raise HTTPException(404, "测验不存在")
    # 检查时间窗口
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if qz.start_at and now < qz.start_at:
        raise HTTPException(400, "测验尚未开始")
    if qz.end_at and now > qz.end_at:
        raise HTTPException(400, "测验已结束，不能提交")
    if db.query(models.QuizAttempt).filter(models.QuizAttempt.quiz_id == quiz_id, models.QuizAttempt.student_id == current_user.id).first():
        raise HTTPException(400, "已作答过该测验")
    # Auto grading
    total = len(qz.questions)
    correct = sum(1 for q in qz.questions if str(q.id) in req.answers and req.answers[str(q.id)] == q.correct_option)
    score = round(correct / total * 100, 1) if total > 0 else 0
    attempt = models.QuizAttempt(quiz_id=quiz_id, student_id=current_user.id, answers=req.answers, score=score)
    db.add(attempt)
    db.commit()
    return {"correct": correct, "total": total, "score": score}


@router.get("/{quiz_id}/stats")
def quiz_stats(quiz_id: int, db: Session = Depends(get_db), _=Depends(require_role("teacher", "admin"))):
    attempts = db.query(models.QuizAttempt).filter(models.QuizAttempt.quiz_id == quiz_id).all()
    if not attempts:
        return {"count": 0, "avg": 0, "max": 0}
    scores = [a.score for a in attempts if a.score is not None]
    return {"count": len(scores), "avg": round(sum(scores)/len(scores), 1) if scores else 0, "max": max(scores) if scores else 0}
