# TTS module initialization
from .tts_interface import TTSInterface
from .openai_tts import OpenAITTS
from .edge_tts import EdgeTTS
from backend.core.config import config


def get_tts_service() -> TTSInterface:
    """
    Get the TTS service based on configuration
    
    Returns:
        TTSInterface: TTS service instance
    """
    tts_service = config.TTS_SERVICE
    
    if tts_service == "openai_tts":
        return OpenAITTS()
    elif tts_service == "edge_tts":
        return EdgeTTS()
    else:
        # Default to Edge TTS for local testing
        return EdgeTTS()