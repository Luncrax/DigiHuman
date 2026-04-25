"""
Vosk ASR implementation for local speech recognition.
"""
import asyncio
import io
import logging
import wave
from pathlib import Path
from typing import Union

import numpy as np

from backend.core.config import config

from .asr_interface import ASRInterface


logger = logging.getLogger(__name__)


class VoskASR(ASRInterface):
    """Vosk ASR implementation for local speech recognition."""

    def __init__(self):
        self.available = False
        self.model = None
        self.recognizer = None

        try:
            from vosk import KaldiRecognizer, Model
            import json

            self.json = json

            project_root = Path(__file__).resolve().parents[2]
            configured_path = Path(config.ASR_VOSK_MODEL_PATH)
            if not configured_path.is_absolute():
                configured_path = project_root / configured_path

            model_paths = [
                configured_path,
                project_root / "models" / "vosk-model-small-cn-0.22",
                project_root / "model",
                Path.cwd() / "model",
                Path.cwd() / "models" / "vosk-model-small-cn-0.22",
            ]

            for path in model_paths:
                try:
                    if not path.exists():
                        logger.warning("Skipping missing Vosk model path: %s", path)
                        continue
                    self.model = Model(str(path))
                    logger.info("Successfully loaded Vosk model from %s", path)
                    break
                except Exception as exc:
                    logger.warning("Failed to load Vosk model from %s: %s", path, exc)

            if self.model:
                self.recognizer = KaldiRecognizer(self.model, 16000)
                self.recognizer.SetWords(True)
                self.available = True
            else:
                logger.warning("Vosk model not found, ASR will fall back to an error prompt")

        except ImportError as exc:
            logger.error("Vosk not installed: %s", exc)

    def _convert_audio_to_wav(self, audio_input: Union[str, bytes, np.ndarray]) -> bytes:
        if isinstance(audio_input, str):
            with open(audio_input, "rb") as audio_file:
                return audio_file.read()

        if isinstance(audio_input, np.ndarray):
            return self._numpy_to_wav_bytes(audio_input)

        if isinstance(audio_input, bytes):
            try:
                with wave.open(io.BytesIO(audio_input), "rb"):
                    return audio_input
            except Exception:
                logger.warning("Received non-WAV audio bytes, attempting to process them directly")
                return audio_input

        raise ValueError(f"Unsupported audio input type: {type(audio_input)}")

    def _numpy_to_wav_bytes(self, audio_array: np.ndarray, sample_rate: int = 16000) -> bytes:
        audio_normalized = np.clip(audio_array, -1.0, 1.0)
        audio_int16 = (audio_normalized * 32767).astype(np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        return wav_buffer.getvalue()

    async def async_transcribe(self, audio_input: Union[str, bytes, np.ndarray]) -> str:
        try:
            wav_bytes = self._convert_audio_to_wav(audio_input)

            if not self.available or not self.recognizer:
                logger.info("Vosk not available, returning configuration hint")
                return "[Vosk模型未找到，请检查 ASR_VOSK_MODEL_PATH 配置]"

            logger.info("Starting Vosk transcription with audio length: %s bytes", len(wav_bytes))

            chunk_size = 8000
            for i in range(0, len(wav_bytes), chunk_size):
                chunk = wav_bytes[i:i + chunk_size]
                self.recognizer.AcceptWaveform(chunk)

            result_str = self.recognizer.FinalResult()
            logger.info("Vosk FinalResult: %s", result_str)

            if not result_str:
                logger.warning("Empty result from Vosk")
                return ""

            try:
                result = self.json.loads(result_str)
                text = result.get("text", "")
                logger.info("Vosk transcription result: %s", text)
                return text
            except Exception as exc:
                logger.error("Failed to parse Vosk result: %s", exc)
                return ""
        except Exception as exc:
            logger.error("Error in Vosk ASR transcription: %s", exc)
            return "[语音识别失败]"

    async def async_transcribe_np(self, audio_array: np.ndarray) -> str:
        try:
            wav_bytes = self._numpy_to_wav_bytes(audio_array)
            return await self.async_transcribe(wav_bytes)
        except Exception as exc:
            logger.error("Error in Vosk ASR transcription: %s", exc)
            return "[语音识别失败]"

    def transcribe(self, audio_input: Union[str, bytes, np.ndarray]) -> str:
        return asyncio.run(self.async_transcribe(audio_input))
