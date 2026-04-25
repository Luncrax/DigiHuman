"""
Edge TTS implementation for low-latency speech synthesis.
"""
import asyncio

from backend.core.config import config

from .tts_interface import TTSInterface


class EdgeTTS(TTSInterface):
    """Edge TTS implementation for text-to-speech."""

    FALLBACK_VOICES = [
        "zh-CN-XiaoxiaoNeural",
        "zh-CN-XiaoyiNeural",
        "zh-CN-liaoning-XiaobeiNeural",
    ]

    def __init__(self):
        try:
            import edge_tts

            self.edge_tts = edge_tts
            self.available = True
        except ImportError as exc:
            self.edge_tts = None
            self.available = False
            print(f"Edge TTS not installed: {exc}")

    async def async_synthesize(
        self,
        text: str,
        voice: str = "zh-CN-YunxiNeural",
        model: str = "edge_tts",
        rate: str | None = None,
        pitch: str | None = None,
        volume: str | None = None,
        **kwargs,
    ) -> bytes:
        if not self.available or not self.edge_tts:
            raise RuntimeError("edge-tts is not installed in the current Python environment")

        requested_voice = voice or config.TTS_VOICE
        voices_to_try = [requested_voice]
        voices_to_try.extend(
            fallback for fallback in self.FALLBACK_VOICES
            if fallback not in voices_to_try
        )

        last_error = None
        for candidate_voice in voices_to_try:
            for attempt in range(2):
                try:
                    communicate = self.edge_tts.Communicate(
                        text=text,
                        voice=candidate_voice,
                        rate=rate or config.EDGE_TTS_RATE,
                        pitch=pitch or config.EDGE_TTS_PITCH,
                        volume=volume or config.EDGE_TTS_VOLUME,
                    )

                    audio_data = bytearray()
                    async for chunk in communicate.stream():
                        if chunk.get("type") == "audio":
                            audio_data.extend(chunk["data"])

                    if audio_data:
                        return bytes(audio_data)
                    last_error = RuntimeError(f"Edge TTS returned no audio for voice {candidate_voice}")
                except Exception as exc:
                    last_error = exc

                if attempt == 0:
                    await asyncio.sleep(0.35)

        raise RuntimeError(f"Edge TTS synthesis failed after retry/fallback: {last_error}")

    def synthesize(
        self,
        text: str,
        voice: str = "zh-CN-YunxiNeural",
        model: str = "edge_tts",
        **kwargs,
    ) -> bytes:
        return asyncio.run(self.async_synthesize(text, voice=voice, model=model, **kwargs))
