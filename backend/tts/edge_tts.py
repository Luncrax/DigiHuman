"""
Edge TTS Implementation for local text-to-speech
"""
import asyncio
from typing import Optional
from .tts_interface import TTSInterface


class EdgeTTS(TTSInterface):
    """Edge TTS implementation for text-to-speech"""
    
    def __init__(self):
        """Initialize Edge TTS"""
        try:
            import edge_tts
            self.edge_tts = edge_tts
            self.available = True
        except ImportError:
            print("Edge TTS not installed, using mock implementation")
            self.available = False
    
    async def async_synthesize(self, text: str, voice: str = "zh-CN-YunxiNeural", 
                             model: str = "tts-1", **kwargs) -> bytes:
        """Asynchronously synthesize text to speech"""
        try:
            if self.available:
                # Use Edge TTS for real synthesis
                communicate = self.edge_tts.Communicate(text, voice)
                audio_data = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data += chunk["data"]
                return audio_data
            else:
                # Mock implementation for testing
                # Return a small silent audio file
                import io
                import wave
                
                # Create a silent WAV file
                buffer = io.BytesIO()
                with wave.open(buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(22050)
                    # 1 second of silence
                    wav_file.writeframes(b'\x00' * 22050 * 2)
                
                buffer.seek(0)
                return buffer.read()
        except Exception as e:
            print(f"Error in Edge TTS synthesis: {e}")
            # Return mock audio
            import io
            import wave
            
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                wav_file.writeframes(b'\x00' * 22050 * 2)
            
            buffer.seek(0)
            return buffer.read()
    
    def synthesize(self, text: str, voice: str = "zh-CN-YunxiNeural", 
                  model: str = "tts-1", **kwargs) -> bytes:
        """Synchronously synthesize text to speech"""
        return asyncio.run(self.async_synthesize(text, voice, model, **kwargs))