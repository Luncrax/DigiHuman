"""
OpenAI Whisper ASR Implementation
Based on open-llm-vtuber's openai_whisper_asr.py
"""
import asyncio
import numpy as np
import io
import wave
from typing import Union
from .asr_interface import ASRInterface
from openai import AsyncOpenAI
from backend.core.config import config


class OpenAIWhisperASR(ASRInterface):
    """OpenAI Whisper ASR implementation"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL
        )
    
    def _numpy_to_wav_bytes(self, audio_array: np.ndarray, sample_rate: int = 16000) -> bytes:
        """Convert numpy array to WAV bytes"""
        # Normalize audio to 16-bit range
        audio_normalized = np.clip(audio_array, -1.0, 1.0)
        audio_int16 = (audio_normalized * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return wav_buffer.getvalue()
    
    async def async_transcribe(self, audio_input: Union[str, bytes]) -> str:
        """Asynchronously transcribe audio to text"""
        try:
            if isinstance(audio_input, str):
                # If it's a file path, read the file
                with open(audio_input, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
            else:
                # If it's already bytes
                audio_bytes = audio_input
            
            # Create a BytesIO object for the file-like object required by OpenAI
            audio_io = io.BytesIO(audio_bytes)
            audio_io.name = "audio.wav"  # Required by OpenAI API
            
            # Transcribe using OpenAI Whisper
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_io
            )
            
            return response.text
        except Exception as e:
            print(f"Error in ASR transcription: {e}")
            return ""
    
    async def async_transcribe_np(self, audio_array: np.ndarray) -> str:
        """Asynchronously transcribe numpy audio array to text"""
        try:
            # Convert numpy array to WAV bytes
            wav_bytes = self._numpy_to_wav_bytes(audio_array)
            
            # Convert to BytesIO for OpenAI API
            audio_io = io.BytesIO(wav_bytes)
            audio_io.name = "audio.wav"
            
            # Transcribe using OpenAI Whisper
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_io
            )
            
            return response.text
        except Exception as e:
            print(f"Error in ASR transcription: {e}")
            return ""
    
    def transcribe(self, audio_input: Union[str, bytes]) -> str:
        """Synchronously transcribe audio to text"""
        # For synchronous operation, we'll use asyncio.run to call the async method
        return asyncio.run(self.async_transcribe(audio_input))
