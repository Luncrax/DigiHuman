"""
Configuration module for Virtual Human Assistant
Contains all configuration settings and environment variables
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dataclasses import dataclass


class Config(BaseSettings):
    # Application settings
    APP_NAME: str = os.getenv("APP_NAME", "Virtual Human Assistant")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Virtual Human Assistant API")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    
    # LLM settings
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "glm-4.6v-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "512"))
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")  # For AsyncLLM
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "c71829a8460f4b51b8d05bb558860179.D2eRQIj3cckGv4BZ")  # For AsyncLLM
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "c71829a8460f4b51b8d05bb558860179.D2eRQIj3cckGv4BZ")
    OPENAI_ORGANIZATION_ID: str = os.getenv("OPENAI_ORGANIZATION_ID", "")
    
    @property
    def LLM_MODEL(self) -> str:
        return self.LLM_MODEL_NAME
    
    # Memory settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    
    # Frontend settings
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: str = os.getenv("BACKEND_CORS_ORIGINS", "*")
    
    @property
    def backend_cors_origins_list(self) -> list:
        """Convert the comma-separated string to a list of origins."""
        if self.BACKEND_CORS_ORIGINS.strip():
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return ["*"]
    
    # ASR/TTS settings
    ASR_ENABLED: bool = os.getenv("ASR_ENABLED", "True").lower() == "true"
    TTS_ENABLED: bool = os.getenv("TTS_ENABLED", "True").lower() == "true"
    ASR_SERVICE: str = os.getenv("ASR_SERVICE", "openai_whisper")  # Options: openai_whisper, vosk, etc.
    TTS_SERVICE: str = os.getenv("TTS_SERVICE", "openai_tts")  # Options: openai_tts, elevenlabs, etc.
    TTS_VOICE: str = os.getenv("TTS_VOICE", "alloy")
    TTS_MODEL: str = os.getenv("TTS_MODEL", "tts-1")
    
    # Live2D settings
    LIVE2D_ENABLED: bool = os.getenv("LIVE2D_ENABLED", "False").lower() == "true"
    LIVE2D_MODEL_PATH: str = os.getenv("LIVE2D_MODEL_PATH", "")
    LIVE2D_MOTION_PATH: str = os.getenv("LIVE2D_MOTION_PATH", "")
    LIVE2D_EXPRESSION_PATH: str = os.getenv("LIVE2D_EXPRESSION_PATH", "")
    LIVE2D_PHYSICS_PATH: str = os.getenv("LIVE2D_PHYSICS_PATH", "")
    LIVE2D_POSE_PATH: str = os.getenv("LIVE2D_POSE_PATH", "")
    
    # WebSocket settings
    WS_MAX_CONNECTIONS: int = int(os.getenv("WS_MAX_CONNECTIONS", "100"))
    WS_TIMEOUT: int = int(os.getenv("WS_TIMEOUT", "300"))  # 5 minutes timeout

    class Config:
        env_file = ".env"


# Create a global config instance
config = Config()


@dataclass
class TTSPreprocessorConfig:
    """Configuration for TTS preprocessor"""
    enabled: bool = True
    remove_punctuation: bool = True
    convert_numbers: bool = True
    normalize_whitespace: bool = True
    max_length: int = 100  # Maximum characters per chunk
    chunk_overlap: int = 10  # Overlap between chunks