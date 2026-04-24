"""
Vosk ASR Implementation for local speech recognition
"""
import asyncio
import numpy as np
import io
import wave
import logging
from typing import Union
from .asr_interface import ASRInterface

# Set up logging
logger = logging.getLogger(__name__)


class VoskASR(ASRInterface):
    """Vosk ASR implementation for local speech recognition"""
    
    def __init__(self):
        """Initialize Vosk ASR"""
        try:
            from vosk import Model, KaldiRecognizer
            import json
            
            # Try to load Vosk model
            # Note: You need to download a Vosk model first
            # Example: https://alphacephei.com/vosk/models
            try:
                # Try different model paths
                model_paths = ["model", "./model", "../model", "models/vosk-model-small-cn-0.22"]
                self.model = None
                
                for path in model_paths:
                    try:
                        self.model = Model(path)
                        logger.info(f"Successfully loaded Vosk model from {path}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load Vosk model from {path}: {e}")
                        continue
                
                if self.model:
                    # Create recognizer with higher sample rate for better accuracy
                    self.recognizer = KaldiRecognizer(self.model, 16000)
                    # Enable partial results for better responsiveness
                    self.recognizer.SetWords(True)  # Enable word-level timestamps
                    self.available = True
                else:
                    logger.warning("Vosk model not found, using mock implementation")
                    self.available = False
                
            except Exception as e:
                logger.error(f"Error initializing Vosk model: {e}")
                self.available = False
            
            self.json = json
        except ImportError as e:
            logger.error(f"Vosk not installed: {e}")
            self.available = False
    
    def _convert_audio_to_wav(self, audio_input: Union[str, bytes, np.ndarray]) -> bytes:
        """
        Convert various audio formats to WAV bytes
        
        Args:
            audio_input: Audio input in various formats
            
        Returns:
            bytes: WAV format audio
        """
        if isinstance(audio_input, str):
            # If it's a file path, read the file
            with open(audio_input, 'rb') as audio_file:
                return audio_file.read()
        elif isinstance(audio_input, np.ndarray):
            # Convert numpy array to WAV bytes
            return self._numpy_to_wav_bytes(audio_input)
        elif isinstance(audio_input, bytes):
            # If it's already bytes, check if it's a valid WAV
            try:
                # Try to open as WAV to verify format
                with wave.open(io.BytesIO(audio_input), 'rb') as wav_file:
                    return audio_input
            except Exception:
                # If not a valid WAV, try to process it
                logger.warning("Received non-WAV audio bytes, attempting to process")
                return audio_input
        else:
            raise ValueError(f"Unsupported audio input type: {type(audio_input)}")
    
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
    
    async def async_transcribe(self, audio_input: Union[str, bytes, np.ndarray]) -> str:
        """
        Asynchronously transcribe audio to text
        
        Args:
            audio_input: Audio input in various formats
            
        Returns:
            str: Transcribed text
        """
        try:
            # Convert audio to WAV format
            wav_bytes = self._convert_audio_to_wav(audio_input)
            
            if self.available:
                # Use Vosk for real transcription
                logger.info(f"Starting Vosk transcription with audio length: {len(wav_bytes)} bytes")
                
                # Process audio in chunks for better memory management
                chunk_size = 8000  # 0.5 seconds at 16kHz
                for i in range(0, len(wav_bytes), chunk_size):
                    chunk = wav_bytes[i:i+chunk_size]
                    self.recognizer.AcceptWaveform(chunk)
                
                # Get final result
                result_str = self.recognizer.FinalResult()
                logger.info(f"Vosk FinalResult: '{result_str}'")
                
                if not result_str:
                    logger.warning("Empty result from Vosk")
                    return ""
                
                try:
                    result = self.json.loads(result_str)
                    text = result.get("text", "")
                    logger.info(f"Vosk transcription result: '{text}'")
                    return text
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Vosk result: {e}")
                    return ""
            else:
                # Mock implementation for testing - return actual audio content
                logger.info("Vosk not available, using mock transcription")
                return "[Vosk模型未找到，请下载并配置Vosk模型]"
        except Exception as e:
            logger.error(f"Error in Vosk ASR transcription: {e}")
            # Return a meaningful error message instead of mock data
            return "[语音识别失败]"
    
    async def async_transcribe_np(self, audio_array: np.ndarray) -> str:
        """
        Asynchronously transcribe numpy audio array to text
        
        Args:
            audio_array: Numpy audio array
            
        Returns:
            str: Transcribed text
        """
        try:
            # Convert numpy array to WAV bytes
            wav_bytes = self._numpy_to_wav_bytes(audio_array)
            
            if self.available:
                # Use Vosk for real transcription
                logger.info(f"Starting Vosk transcription with numpy array shape: {audio_array.shape}")
                
                # Process audio in chunks
                chunk_size = 8000
                for i in range(0, len(wav_bytes), chunk_size):
                    chunk = wav_bytes[i:i+chunk_size]
                    self.recognizer.AcceptWaveform(chunk)
                
                result = self.json.loads(self.recognizer.FinalResult())
                text = result.get("text", "")
                
                logger.info(f"Vosk transcription result: {text}")
                return text
            else:
                # Mock implementation for testing
                logger.info("Vosk not available, using mock transcription")
                return "你好，这是一个测试消息"
        except Exception as e:
            logger.error(f"Error in Vosk ASR transcription: {e}")
            return "[语音识别失败]"
    
    def transcribe(self, audio_input: Union[str, bytes, np.ndarray]) -> str:
        """
        Synchronously transcribe audio to text
        
        Args:
            audio_input: Audio input in various formats
            
        Returns:
            str: Transcribed text
        """
        # For synchronous operation, we'll use asyncio.run to call the async method
        return asyncio.run(self.async_transcribe(audio_input))