"""
Qwen3-TTS client for DigiHuman.
Bridges the Windows backend to a custom Qwen3-TTS service running inside WSL.
"""
import asyncio
import base64
import json
from typing import Any, Dict, Optional, Tuple
from urllib import error, request

from backend.core.config import config

from .tts_interface import TTSInterface


class Qwen3TTS(TTSInterface):
    """HTTP client for the custom Qwen3-TTS WSL service."""

    MODEL_ALIASES = {
        "base": "base",
        "qwen_base": "base",
        "prompt_clone": "base",
        "voice_clone": "base",
        "custom": "custom_voice",
        "custom_voice": "custom_voice",
        "voice": "custom_voice",
        "design": "voice_design",
        "voice_design": "voice_design",
        "tts-1": "base",
    }

    EMOTION_INSTRUCT = {
        "happy": "Speak in a bright, delighted, lively tone.",
        "joy": "Speak in a bright, delighted, lively tone.",
        "sad": "Speak in a soft, slightly sad, low-energy tone.",
        "sadness": "Speak in a soft, slightly sad, low-energy tone.",
        "angry": "Speak with restrained anger, firm emphasis, and controlled intensity.",
        "anger": "Speak with restrained anger, firm emphasis, and controlled intensity.",
        "shy": "Speak in a gentle, hesitant, shy tone.",
        "surprised": "Speak with surprise and a touch of urgency.",
        "surprise": "Speak with surprise and a touch of urgency.",
        "fear": "Speak with tension and slight nervousness.",
        "scared": "Speak with tension and slight nervousness.",
        "neutral": "",
    }

    def _resolve_mode_and_path(self, model: Optional[str]) -> Tuple[str, str]:
        normalized = self.MODEL_ALIASES.get((model or config.TTS_MODEL or "base").strip().lower(), "base")
        if normalized == "base" and config.QWEN3_TTS_PROMPT_PATH:
            return "base", config.QWEN3_TTS_BASE_MODEL_PATH
        if normalized == "custom_voice":
            return normalized, config.QWEN3_TTS_CUSTOM_MODEL_PATH
        if normalized == "voice_design":
            return normalized, config.QWEN3_TTS_DESIGN_MODEL_PATH
        return "base", config.QWEN3_TTS_BASE_MODEL_PATH

    def _build_instruct(self, emotion: Optional[str], intensity: Optional[str], override: Optional[str]) -> Optional[str]:
        if override:
            return override

        base = self.EMOTION_INSTRUCT.get((emotion or "neutral").lower(), "")
        if not base:
            return None

        if intensity == "high":
            return f"{base} Make the emotional color very obvious."
        if intensity == "low":
            return f"{base} Keep the expression subtle and natural."
        return base

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{config.QWEN3_TTS_SERVER_URL.rstrip('/')}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=600) as resp:
                raw = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Qwen3-TTS server returned HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(
                "Qwen3-TTS server is unreachable. Start the WSL service first."
            ) from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON from Qwen3-TTS server: {raw[:200]}") from exc

    async def async_synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        emotion: Optional[str] = None,
        intensity: Optional[str] = None,
        instruct: Optional[str] = None,
        language: Optional[str] = None,
        voice_prompt_path: Optional[str] = None,
        **kwargs,
    ) -> bytes:
        mode, model_path = self._resolve_mode_and_path(model)

        payload: Dict[str, Any] = {
            "text": text,
            "mode": mode,
            "model_path": model_path,
            "source_path": config.QWEN3_TTS_SOURCE_PATH,
            "language": language or config.QWEN3_TTS_LANGUAGE,
            "speaker": voice or config.QWEN3_TTS_CUSTOM_SPEAKER,
            "instruct": self._build_instruct(emotion, intensity, instruct),
            "prompt_path": voice_prompt_path or config.QWEN3_TTS_PROMPT_PATH or None,
            "device": config.QWEN3_TTS_DEVICE,
            "dtype": config.QWEN3_TTS_DTYPE,
            "flash_attn": config.QWEN3_TTS_FLASH_ATTN,
        }
        payload.update({k: v for k, v in kwargs.items() if v is not None})

        result = await asyncio.to_thread(self._post_json, "/synthesize", payload)
        audio_b64 = result.get("audio_base64")
        if not audio_b64:
            raise RuntimeError(f"Qwen3-TTS server returned no audio: {result}")
        return base64.b64decode(audio_b64)

    def synthesize(self, text: str, **kwargs) -> bytes:
        return asyncio.run(self.async_synthesize(text, **kwargs))
