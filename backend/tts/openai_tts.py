"""
OpenAI TTS Implementation
Based on open-llm-vtuber's openai_tts.py
"""
import asyncio
import numpy as np
import io
from typing import Union
from .tts_interface import TTSInterface
from openai import AsyncOpenAI
from backend.core.config import config


class OpenAITTS(TTSInterface):
    """OpenAI TTS implementation"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL
        )
        self.default_voice = "alloy"  # Default voice for OpenAI TTS
        self.default_model = "tts-1"  # Default model for OpenAI TTS
    
    async def async_synthesize(self, text: str, voice: str = None, model: str = None) -> Union[bytes, np.ndarray]:
        """Asynchronously synthesize text to audio"""
        try:
            if voice is None:
                voice = self.default_voice
            if model is None:
                model = self.default_model
            
            # Synthesize using OpenAI TTS
            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            
            # Get audio content as bytes
            audio_bytes = response.content
            
            return audio_bytes
        except Exception as e:
            print(f"Error in TTS synthesis: {e}")
            return b""
    
    def synthesize(self, text: str, voice: str = None, model: str = None) -> Union[bytes, np.ndarray]:
        """Synchronously synthesize text to audio"""
        # For synchronous operation, we'll use asyncio.run to call the async method
        return asyncio.run(self.async_synthesize(text, voice, model))
