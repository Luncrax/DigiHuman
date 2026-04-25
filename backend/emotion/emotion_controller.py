"""
Emotion controller for DigiHuman.
Turns analyzed emotion into executable text, TTS, and Live2D controls.
"""
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from backend.character_config import get_character_config
from backend.core.config import config
from backend.emotion.langchain_emotion_analyzer import EmotionAnalysisResult
from backend.live2d.emotion_mapper import get_emotion_mapper


@dataclass
class EmotionControlResult:
    enhanced_text: str
    tts_params: Dict[str, Any]
    tts_instruct: Optional[str]
    live2d_params: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EmotionController:
    """Central orchestration for emotion-driven output controls."""

    EMOTION_ALIASES = {
        "happy": "joy",
        "joy": "joy",
        "sad": "sadness",
        "sadness": "sadness",
        "angry": "anger",
        "anger": "anger",
        "surprised": "surprise",
        "surprise": "surprise",
        "fear": "fear",
        "scared": "fear",
        "disgust": "disgust",
        "shy": "shy",
        "neutral": "neutral",
    }

    INTENSITY_ALIASES = {
        "low": "low",
        "medium": "medium",
        "high": "high",
    }

    EMOTION_INSTRUCT = {
        "joy": {
            "low": "Speak in a warm, lightly cheerful tone with a gentle smile in the voice.",
            "medium": "Speak in a bright, delighted, lively tone.",
            "high": "Speak in an excited, sparkling, highly joyful tone without sounding chaotic.",
        },
        "sadness": {
            "low": "Speak softly with a faint sense of sadness and reduced energy.",
            "medium": "Speak in a soft, slightly sad, low-energy tone.",
            "high": "Speak in a fragile, clearly sorrowful tone with slow, weighted phrasing.",
        },
        "anger": {
            "low": "Speak firmly with restrained displeasure and controlled emphasis.",
            "medium": "Speak with restrained anger, firm emphasis, and controlled intensity.",
            "high": "Speak with intense but controlled anger, stronger stress, and sharp emotional color.",
        },
        "surprise": {
            "low": "Speak with mild surprise and a slightly lifted tone.",
            "medium": "Speak with surprise and a touch of urgency.",
            "high": "Speak with obvious astonishment and energetic, lifted phrasing.",
        },
        "fear": {
            "low": "Speak with slight nervousness and careful pacing.",
            "medium": "Speak with tension and slight nervousness.",
            "high": "Speak in a tense, uneasy tone with audible hesitation and fragile confidence.",
        },
        "disgust": {
            "low": "Speak with light aversion and subtle distance.",
            "medium": "Speak with clear dislike and restrained coldness.",
            "high": "Speak with strong disgust, clipped emphasis, and obvious rejection.",
        },
        "shy": {
            "low": "Speak gently and a little reserved, with soft pacing.",
            "medium": "Speak in a gentle, hesitant, shy tone.",
            "high": "Speak in a timid, bashful tone with noticeable hesitation and softness.",
        },
        "neutral": {
            "low": "Speak naturally and calmly.",
            "medium": "Speak naturally and calmly.",
            "high": "Speak clearly and steadily, but remain emotionally neutral.",
        },
    }

    def __init__(self):
        self.emotion_mapper = get_emotion_mapper()

    def normalize_emotion(self, emotion: Optional[str]) -> str:
        if not emotion:
            return "neutral"
        return self.EMOTION_ALIASES.get(str(emotion).strip().lower(), "neutral")

    def normalize_intensity(self, intensity: Optional[str]) -> str:
        if not intensity:
            return "medium"
        return self.INTENSITY_ALIASES.get(str(intensity).strip().lower(), "medium")

    def build_controls(
        self,
        text: str,
        emotion: Optional[str],
        intensity: Optional[str],
        confidence: float = 0.5,
        details: Optional[Dict[str, float]] = None,
    ) -> EmotionControlResult:
        normalized_emotion = self.normalize_emotion(emotion)
        normalized_intensity = self.normalize_intensity(intensity)
        enhanced_text = self._enhance_text(text or "", normalized_emotion, normalized_intensity)
        tts_instruct = self._build_tts_instruct(normalized_emotion, normalized_intensity)
        tts_params = self._build_tts_params(normalized_emotion, normalized_intensity, tts_instruct)
        live2d_params = self._build_live2d_params(
            enhanced_text,
            normalized_emotion,
            normalized_intensity,
            confidence,
            details,
        )

        return EmotionControlResult(
            enhanced_text=enhanced_text,
            tts_params=tts_params,
            tts_instruct=tts_instruct,
            live2d_params=live2d_params,
        )

    def build_from_analysis(self, text: str, emotion_result: EmotionAnalysisResult) -> EmotionControlResult:
        return self.build_controls(
            text=text,
            emotion=getattr(emotion_result, "emotion", None),
            intensity=getattr(emotion_result, "intensity", None),
            confidence=float(getattr(emotion_result, "confidence", 0.5) or 0.5),
            details=getattr(emotion_result, "details", None),
        )

    def _enhance_text(self, text: str, emotion: str, intensity: str) -> str:
        stripped = (text or "").strip()
        if not stripped:
            return ""

        if emotion == "joy":
            if intensity == "high" and not stripped.endswith(("!!", "！！")):
                return f"{stripped}！！"
            if intensity == "medium" and not stripped.endswith(("!", "！")):
                return f"{stripped}！"
            if intensity == "low" and not stripped.endswith(("。", ".", "!", "！", "呀")):
                return f"{stripped}呀。"
            return stripped

        if emotion == "sadness":
            if not stripped.endswith(("...", "……")):
                return f"{stripped}……"
            return stripped

        if emotion == "surprise":
            if intensity == "high" and not stripped.endswith(("?!", "？！")):
                return f"{stripped}？！"
            if not stripped.endswith(("?", "？", "!", "！")):
                return f"{stripped}？"
            return stripped

        if emotion in {"fear", "shy"}:
            if not stripped.startswith(("嗯", "那个", "um", "well")):
                prefix = "嗯，" if intensity == "low" else "那个……"
                return f"{prefix}{stripped}"
            return stripped

        if emotion == "anger":
            if intensity in {"medium", "high"} and not stripped.endswith(("!", "！")):
                return f"{stripped}！"
            return stripped

        return stripped

    def _build_tts_instruct(self, emotion: str, intensity: str) -> Optional[str]:
        if not config.QWEN3_TTS_ENABLE_STYLE:
            return None
        base_instruct = self.EMOTION_INSTRUCT.get(emotion, self.EMOTION_INSTRUCT["neutral"]).get(intensity)
        emotion_style = get_character_config().emotion_style.strip()
        if emotion_style and base_instruct:
            return f"{base_instruct} Overall expression style: {emotion_style}"
        if emotion_style:
            return emotion_style
        return base_instruct

    def _build_tts_params(self, emotion: str, intensity: str, instruct: Optional[str]) -> Dict[str, Any]:
        mode = self._select_qwen_mode(emotion, intensity)
        prompt_path = self._select_voice_prompt(mode)
        sampling = self._build_sampling_params(mode, intensity)
        tts_emotion = emotion if config.QWEN3_TTS_ENABLE_STYLE else "neutral"
        tts_intensity = intensity if config.QWEN3_TTS_ENABLE_STYLE else "low"
        tts_instruct = instruct if config.QWEN3_TTS_ENABLE_STYLE else None

        params: Dict[str, Any] = {
            "voice": config.TTS_VOICE,
            "model": config.TTS_MODEL,
            "emotion": tts_emotion,
            "intensity": tts_intensity,
            "language": config.QWEN3_TTS_LANGUAGE,
            "voice_prompt_path": prompt_path,
            "instruct": tts_instruct,
            "speaker": config.QWEN3_TTS_CUSTOM_SPEAKER or config.TTS_VOICE,
            "strategy": {
                "mode": mode,
                "speaker": config.QWEN3_TTS_CUSTOM_SPEAKER or config.TTS_VOICE,
                "prompt_path": prompt_path,
                "emotion": tts_emotion,
                "intensity": tts_intensity,
                "style_enabled": bool(config.QWEN3_TTS_ENABLE_STYLE),
            },
        }
        params.update(sampling)

        if config.TTS_SERVICE == "qwen3_tts":
            params["voice"] = params["speaker"]
            params["model"] = mode
        else:
            params["model"] = config.TTS_MODEL
            params["voice_prompt_path"] = None
            params["instruct"] = None
            params["speaker"] = None

        return params

    def _select_qwen_mode(self, emotion: str, intensity: str) -> str:
        configured = (config.TTS_MODEL or "custom_voice").strip().lower()
        if configured in {"prompt_clone", "voice_clone"}:
            configured = "base"

        allowed = {"base", "custom_voice", "voice_design"}

        if configured in allowed:
            if configured == "base":
                if config.QWEN3_TTS_PROMPT_PATH:
                    return "base"
                return "custom_voice"
            return configured

        if config.QWEN3_TTS_PROMPT_PATH and emotion == "neutral" and intensity == "low":
            return "base"
        if emotion in {"anger", "surprise", "joy"} and intensity == "high":
            return "voice_design"
        if emotion in {"shy", "fear", "sadness"}:
            return "custom_voice"
        return "custom_voice"

    def _select_voice_prompt(self, mode: str) -> Optional[str]:
        if mode == "base" and config.QWEN3_TTS_PROMPT_PATH:
            return config.QWEN3_TTS_PROMPT_PATH
        return None

    def _build_sampling_params(self, mode: str, intensity: str) -> Dict[str, Any]:
        if mode == "voice_design":
            if intensity == "high":
                return {
                    "temperature": 0.85,
                    "top_p": 0.86,
                    "top_k": 24,
                    "repetition_penalty": 1.05,
                    "max_new_tokens": 320,
                }
            return {
                "temperature": 0.76,
                "top_p": 0.82,
                "top_k": 20,
                "repetition_penalty": 1.03,
                "max_new_tokens": 280,
            }

        if mode == "custom_voice":
            if intensity == "high":
                return {
                    "temperature": 0.68,
                    "top_p": 0.8,
                    "top_k": 18,
                    "repetition_penalty": 1.02,
                    "max_new_tokens": 260,
                }
            if intensity == "low":
                return {
                    "temperature": 0.5,
                    "top_p": 0.72,
                    "top_k": 12,
                    "repetition_penalty": 1.01,
                    "max_new_tokens": 220,
                }
            return {
                "temperature": 0.58,
                "top_p": 0.76,
                "top_k": 16,
                "repetition_penalty": 1.01,
                "max_new_tokens": 240,
            }

        return {
            "temperature": 0.45,
            "top_p": 0.68,
            "top_k": 10,
            "repetition_penalty": 1.0,
            "max_new_tokens": 180,
        }

    def _build_live2d_params(
        self,
        text: str,
        emotion: str,
        intensity: str,
        confidence: float,
        details: Optional[Dict[str, float]],
    ) -> Dict[str, Any]:
        emotion_result = EmotionAnalysisResult(
            emotion=emotion,
            confidence=max(0.0, min(1.0, confidence)),
            details=details or {emotion: max(0.0, min(1.0, confidence))},
            intensity=intensity,
        )
        params = self.emotion_mapper.get_action_for_text(text, emotion_result)
        idle_motion = self._select_idle_motion(emotion)
        talk_motion = self._select_talk_motion(emotion)
        react_motion = params.get("motion") or self._select_react_motion(emotion, intensity)
        speech_duration_ms = self._estimate_speech_duration_ms(text, intensity)

        params["state"] = "react" if emotion != "neutral" else "idle"
        params["source"] = "emotion-controller"
        params["priority"] = 2 if emotion != "neutral" else 0
        params["transition_ms"] = 320 if intensity == "low" else 420 if intensity == "medium" else 520
        params["speech_duration_ms"] = speech_duration_ms
        params["recover_to"] = "idle"
        params["idle_motion"] = idle_motion
        params["talk_motion"] = talk_motion
        params["react_motion"] = react_motion
        params["idle_expression"] = "exp_01" if emotion == "neutral" else params.get("expression", "exp_01")
        params["talk_expression"] = params.get("expression", "exp_01")
        params["idle_parameters"] = self._build_idle_parameters(params.get("parameters", {}), emotion)
        params["talk_parameters"] = self._build_talk_parameters(params.get("parameters", {}), emotion, intensity)
        params["react_parameters"] = dict(params.get("parameters", {}))
        return params

    def _select_idle_motion(self, emotion: str) -> str:
        return {
            "joy": "idle_happy",
            "sadness": "idle_sad",
            "fear": "idle_shy",
            "shy": "idle_shy",
        }.get(emotion, "idle")

    def _select_talk_motion(self, emotion: str) -> str:
        return {
            "joy": "talk_bright",
            "sadness": "talk_soft",
            "anger": "talk_firm",
            "disgust": "talk_firm",
            "shy": "talk_shy",
            "fear": "talk_soft",
        }.get(emotion, "talk")

    def _select_react_motion(self, emotion: str, intensity: str) -> str:
        if emotion == "joy":
            return "excited" if intensity == "high" else "talk_bright"
        if emotion == "sadness":
            return "react_sad"
        if emotion == "anger":
            return "react_anger_strong" if intensity == "high" else "react_anger"
        if emotion == "surprise":
            return "react_surprise_big" if intensity == "high" else "react_surprise"
        if emotion == "fear":
            return "react_fear"
        if emotion == "disgust":
            return "react_disgust"
        if emotion == "shy":
            return "react_shy"
        return "idle"

    def _estimate_speech_duration_ms(self, text: str, intensity: str) -> int:
        base_chars = max(len(text or ""), 1)
        per_char = {"low": 170, "medium": 145, "high": 125}.get(intensity, 145)
        return max(1200, min(7000, base_chars * per_char))

    def _build_idle_parameters(self, parameters: Dict[str, Any], emotion: str) -> Dict[str, float]:
        idle = dict(parameters or {})
        idle["mouth_open"] = 0.0
        idle["breath"] = max(0.25, min(0.6, float(idle.get("breath", 0.4))))
        if emotion == "neutral":
            idle["angle_x"] = 0.0
            idle["angle_y"] = 0.0
            idle["angle_z"] = 0.0
        return idle

    def _build_talk_parameters(self, parameters: Dict[str, Any], emotion: str, intensity: str) -> Dict[str, float]:
        talk = dict(parameters or {})
        talk["mouth_open"] = {"low": 0.18, "medium": 0.28, "high": 0.38}.get(intensity, 0.28)
        talk["breath"] = max(float(talk.get("breath", 0.4)), 0.38)
        if emotion == "sadness":
            talk["mouth_open"] = min(talk["mouth_open"], 0.24)
        return talk


_emotion_controller: Optional[EmotionController] = None


def get_emotion_controller() -> EmotionController:
    global _emotion_controller
    if _emotion_controller is None:
        _emotion_controller = EmotionController()
    return _emotion_controller
