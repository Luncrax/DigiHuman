# TTS module initialization
from .tts_interface import TTSInterface
from backend.core.config import config


def get_tts_service() -> TTSInterface:
    """
    Get the TTS service based on configuration
    
    Returns:
        TTSInterface: TTS service instance
    """
    tts_service = config.TTS_SERVICE
    
    if tts_service == "openai_tts":
        from .openai_tts import OpenAITTS
        return OpenAITTS()
    elif tts_service == "edge_tts":
        from .edge_tts import EdgeTTS
        return EdgeTTS()
    elif tts_service == "qwen3_tts":
        from .qwen3_tts import Qwen3TTS
        return Qwen3TTS()
    else:
        # Default to Edge TTS for local testing
        from .edge_tts import EdgeTTS
        return EdgeTTS()
