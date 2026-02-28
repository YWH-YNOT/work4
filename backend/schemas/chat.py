from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    course_id: int
    conversation_id: str
