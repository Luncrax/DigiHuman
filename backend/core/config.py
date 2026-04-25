"""
Configuration module for Virtual Human Assistant
Contains all configuration settings and environment variables.
"""
from dataclasses import dataclass

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_bool(value, default: bool) -> bool:
    """Parse loose boolean-like environment values safely."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default

    normalized = str(value).strip().lower()
    truthy = {"1", "true", "yes", "on", "debug", "development", "dev"}
    falsy = {"0", "false", "no", "off", "release", "prod", "production"}

    if normalized in truthy:
        return True
    if normalized in falsy:
        return False
    return default


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = "Virtual Human Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Virtual Human Assistant API"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # LLM settings
    LLM_MODEL_NAME: str = "glm-4.6v-flash"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 512
    LLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    LLM_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    OPENAI_API_KEY: str = ""
    OPENAI_ORGANIZATION_ID: str = ""
    
    @property
    def LLM_MODEL(self) -> str:
        return self.LLM_MODEL_NAME
    
    # Memory settings
    REDIS_URL: str = "redis://localhost:6379"
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    
    # Frontend settings
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: str = "*"
    
    @property
    def backend_cors_origins_list(self) -> list:
        """Convert the comma-separated string to a list of origins."""
        if self.BACKEND_CORS_ORIGINS.strip():
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return ["*"]
    
    # ASR/TTS settings
    ASR_ENABLED: bool = True
    TTS_ENABLED: bool = True
    ASR_SERVICE: str = "openai_whisper"  # Options: openai_whisper, vosk, etc.
    ASR_VOSK_MODEL_PATH: str = "models/vosk-model-small-cn-0.22"
    TTS_SERVICE: str = "openai_tts"  # Options: openai_tts, elevenlabs, etc.
    TTS_VOICE: str = "alloy"
    TTS_MODEL: str = "tts-1"
    EDGE_TTS_RATE: str = "+0%"
    EDGE_TTS_PITCH: str = "+0Hz"
    EDGE_TTS_VOLUME: str = "+0%"
    QWEN3_TTS_SERVER_URL: str = "http://127.0.0.1:8010"
    QWEN3_TTS_SOURCE_PATH: str = "/mnt/e/big_work/Qwen3-TTS-main"
    QWEN3_TTS_BASE_MODEL_PATH: str = "/mnt/e/big_work/Qwen3-TTS-main/model/base/qwen/Base"
    QWEN3_TTS_CUSTOM_MODEL_PATH: str = "/mnt/e/big_work/Qwen3-TTS-main/model/custom/qwen/CustomVoice"
    QWEN3_TTS_DESIGN_MODEL_PATH: str = "/mnt/e/big_work/Qwen3-TTS-main/model/design/qwen/VoiceDesign"
    QWEN3_TTS_PROMPT_PATH: str = ""
    QWEN3_TTS_LANGUAGE: str = "Auto"
    QWEN3_TTS_CUSTOM_SPEAKER: str = "Vivian"
    QWEN3_TTS_DEVICE: str = "cuda:0"
    QWEN3_TTS_DTYPE: str = "bfloat16"
    QWEN3_TTS_FLASH_ATTN: bool = True
    QWEN3_TTS_ENABLE_STYLE: bool = False
    QWEN3_TTS_WSL_DISTRO: str = "ubuntu"
    QWEN3_TTS_WSL_VENV: str = "flash_env"
    
    # Live2D settings
    LIVE2D_ENABLED: bool = False
    LIVE2D_MODEL_PATH: str = ""
    LIVE2D_MOTION_PATH: str = ""
    LIVE2D_EXPRESSION_PATH: str = ""
    LIVE2D_PHYSICS_PATH: str = ""
    LIVE2D_POSE_PATH: str = ""
    
    # WebSocket settings
    WS_MAX_CONNECTIONS: int = 100
    WS_TIMEOUT: int = 300  # 5 minutes timeout
    EMOTION_ANALYSIS_TIMEOUT: float = 1.2

    @field_validator("DEBUG", "ASR_ENABLED", "TTS_ENABLED", "LIVE2D_ENABLED", "QWEN3_TTS_FLASH_ATTN", "QWEN3_TTS_ENABLE_STYLE", mode="before")
    @classmethod
    def parse_bool_fields(cls, value, info):
        defaults = {
            "DEBUG": False,
            "ASR_ENABLED": True,
            "TTS_ENABLED": True,
            "LIVE2D_ENABLED": False,
            "QWEN3_TTS_FLASH_ATTN": True,
            "QWEN3_TTS_ENABLE_STYLE": False,
        }
        return _parse_bool(value, defaults[info.field_name])


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
