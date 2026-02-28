"""AI 对话路由 - 使用 JWT 认证，持久化 ChatLog"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import logging

from core.database import get_db
from core.auth import get_current_user
from models import core as models
from services.agent_service import AgentService

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    course_id: Optional[int] = None
    conversation_id: Optional[str] = None


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 验证课程访问权限（可选）
    if request.course_id:
        course = db.query(models.Course).filter(models.Course.id == request.course_id).first()
        if not course:
            raise HTTPException(404, "课程不存在")

    # 获取最近 6 轮对话作为上下文
    history = []
    if request.conversation_id:
        logs = (
            db.query(models.ChatLog)
            .filter(models.ChatLog.conversation_id == request.conversation_id)
            .order_by(models.ChatLog.created_at.desc())
            .limit(12)
            .all()
        )
        for log in reversed(logs):
            history.append({"role": log.role, "content": log.content})

    # 持久化用户消息
    user_log = models.ChatLog(
        user_id=current_user.id,
        course_id=request.course_id,
        role="user",
        content=request.message,
        conversation_id=request.conversation_id or "default",
    )
    db.add(user_log)
    db.commit()

    agent = AgentService()
    full_response = ""

    async def generate():
        nonlocal full_response
        try:
            async for chunk in agent.stream_chat(request.message, history, request.course_id):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Agent stream error: {e}")
            yield f"data: {json.dumps({'content': f'系统错误: {str(e)}'})}\n\n"
        finally:
            # 持久化助教回复
            assistant_log = models.ChatLog(
                user_id=current_user.id,
                course_id=request.course_id,
                role="assistant",
                content=full_response,
                conversation_id=request.conversation_id or "default",
            )
            db.add(assistant_log)
            db.commit()
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
