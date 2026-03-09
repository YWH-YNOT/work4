import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI_YWH_Agentic"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Switch to Local SQLite for MVP to bypass Docker requirements
        return "sqlite:///./ai_ywh.db"
    
    # Security
    SECRET_KEY: str = "SUPER_SECRET_KEY_REPLACE_IN_PROD"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # ChromaDB (RAG)
    CHROMA_SERVER_HOST: str = os.getenv("CHROMA_SERVER_HOST", "localhost")
    CHROMA_SERVER_PORT: str = os.getenv("CHROMA_SERVER_PORT", "8000")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Jetson 姿态检测服务地址
    JETSON_IP:   str = "192.168.1.100"
    JETSON_PORT: str = "5000"

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
