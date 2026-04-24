# ASR module initialization
from .asr_interface import ASRInterface
from .openai_whisper_asr import OpenAIWhisperASR
from .vosk_asr import VoskASR
from backend.core.config import config


def get_asr_service() -> ASRInterface:
    """
    Get the ASR service based on configuration
    
    Returns:
        ASRInterface: ASR service instance
    """
    asr_service = config.ASR_SERVICE
    
    if asr_service == "openai_whisper":
        return OpenAIWhisperASR()
    elif asr_service == "vosk":
        return VoskASR()
    else:
        # Default to Vosk for local testing
        return VoskASR()