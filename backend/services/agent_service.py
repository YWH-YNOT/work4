"""
AgentService - 简单的 DeepSeek 流式对话服务
替代旧的 LangChain AgenticTutor，保持与 routers/chat.py 的接口兼容性
"""
import os
import json
import logging
import httpx
from typing import List, Optional, AsyncGenerator
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")

    async def stream_chat(
        self,
        user_message: str,
        history: List[dict],
        course_id: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式调用 DeepSeek chat 接口，逐 chunk 产出文本片段
        """
        system_prompt = (
            "你是一位大学课程的 AI 智能助教，由 DeepSeek 大模型驱动。"
            "请用中文回答学生问题，简洁明了，专业准确。"
            "如果涉及代码，请使用 Markdown 代码块格式。"
        )
        if course_id:
            system_prompt += f" 当前课程ID: {course_id}。"

        messages = [{"role": "system", "content": system_prompt}]
        for h in history[-12:]:  # 最近6轮
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
