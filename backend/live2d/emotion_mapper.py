"""
Emotion-to-Live2D mapping.
Converts analyzed emotion into a softer, more natural Live2D command set.
"""
from dataclasses import dataclass
from typing import Any, Dict

from backend.emotion.langchain_emotion_analyzer import EmotionAnalysisResult
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Live2DAction:
    expression: str
    motion: str
    parameters: Dict[str, float]
    duration: float


class EmotionActionMapper:
    """Maps emotions to expressions, motions, and pose parameters."""

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
        "neutral": "neutral",
        "shy": "shy",
    }

    EMOTION_PROFILES = {
        "joy": {
            "expressions": {"low": "exp_01", "medium": "exp_02", "high": "exp_02"},
            "motions": {"low": "idle_happy", "medium": "talk_bright", "high": "excited"},
            "parameters": {
                "angle_x": 0.08,
                "angle_y": -0.10,
                "angle_z": -0.04,
                "eye_l_open": 1.0,
                "eye_r_open": 1.0,
                "eye_ball_x": 0.02,
                "mouth_open": 0.32,
                "breath": 0.55,
            },
        },
        "sadness": {
            "expressions": {"low": "exp_03", "medium": "exp_03", "high": "exp_04"},
            "motions": {"low": "idle_sad", "medium": "talk_soft", "high": "react_sad"},
            "parameters": {
                "angle_x": -0.04,
                "angle_y": 0.20,
                "angle_z": 0.03,
                "eye_l_open": 0.72,
                "eye_r_open": 0.72,
                "eye_ball_y": 0.10,
                "mouth_open": 0.10,
                "breath": 0.22,
            },
        },
        "anger": {
            "expressions": {"low": "exp_05", "medium": "exp_06", "high": "exp_06"},
            "motions": {"low": "talk_firm", "medium": "react_anger", "high": "react_anger_strong"},
            "parameters": {
                "angle_x": 0.03,
                "angle_y": -0.02,
                "angle_z": 0.06,
                "eye_l_open": 0.88,
                "eye_r_open": 0.88,
                "eye_ball_x": -0.04,
                "mouth_open": 0.26,
                "breath": 0.58,
            },
        },
        "surprise": {
            "expressions": {"low": "exp_07", "medium": "exp_07", "high": "exp_08"},
            "motions": {"low": "react_surprise", "medium": "react_surprise", "high": "react_surprise_big"},
            "parameters": {
                "angle_y": -0.14,
                "eye_l_open": 1.0,
                "eye_r_open": 1.0,
                "eye_ball_y": -0.04,
                "mouth_open": 0.48,
                "breath": 0.42,
            },
        },
        "fear": {
            "expressions": {"low": "exp_07", "medium": "exp_07", "high": "exp_08"},
            "motions": {"low": "idle_shy", "medium": "react_fear", "high": "react_fear"},
            "parameters": {
                "angle_x": -0.06,
                "angle_y": 0.12,
                "angle_z": -0.03,
                "eye_l_open": 0.92,
                "eye_r_open": 0.92,
                "eye_ball_x": 0.03,
                "mouth_open": 0.18,
                "breath": 0.34,
            },
        },
        "disgust": {
            "expressions": {"low": "exp_05", "medium": "exp_05", "high": "exp_06"},
            "motions": {"low": "talk_firm", "medium": "react_disgust", "high": "react_disgust"},
            "parameters": {
                "angle_x": 0.12,
                "angle_z": 0.08,
                "eye_l_open": 0.76,
                "eye_r_open": 0.76,
                "eye_ball_x": -0.08,
                "mouth_open": 0.12,
                "breath": 0.30,
            },
        },
        "shy": {
            "expressions": {"low": "exp_01", "medium": "exp_03", "high": "exp_03"},
            "motions": {"low": "idle_shy", "medium": "talk_shy", "high": "react_shy"},
            "parameters": {
                "angle_x": -0.08,
                "angle_y": 0.08,
                "angle_z": -0.08,
                "eye_l_open": 0.82,
                "eye_r_open": 0.82,
                "eye_ball_x": 0.05,
                "mouth_open": 0.16,
                "breath": 0.28,
            },
        },
        "neutral": {
            "expressions": {"low": "exp_01", "medium": "exp_01", "high": "exp_01"},
            "motions": {"low": "idle", "medium": "talk", "high": "talk"},
            "parameters": {
                "angle_x": 0.0,
                "angle_y": 0.0,
                "angle_z": 0.0,
                "eye_l_open": 1.0,
                "eye_r_open": 1.0,
                "eye_ball_x": 0.0,
                "eye_ball_y": 0.0,
                "mouth_open": 0.16,
                "breath": 0.40,
            },
        },
    }

    INTENSITY_MULTIPLIER = {
        "low": 0.65,
        "medium": 1.0,
        "high": 1.25,
    }

    DURATION_MAP = {
        "low": 1.8,
        "medium": 2.7,
        "high": 3.6,
    }

    def __init__(self):
        logger.info("EmotionActionMapper initialized")

    def map_emotion_to_action(self, emotion_result: EmotionAnalysisResult) -> Live2DAction:
        emotion = self._normalize_emotion(emotion_result.emotion)
        intensity = emotion_result.intensity if emotion_result.intensity in self.INTENSITY_MULTIPLIER else "medium"
        confidence = max(0.0, min(1.0, emotion_result.confidence))

        expression = self._get_expression(emotion, intensity)
        motion = self._get_motion(emotion, intensity)
        parameters = self._get_parameters(emotion, intensity, confidence)
        duration = self.DURATION_MAP.get(intensity, 2.7)

        logger.info(
            f"Mapped emotion {emotion_result.emotion} -> {emotion} ({intensity}, {confidence:.2f}) "
            f"to expression={expression}, motion={motion}"
        )

        return Live2DAction(
            expression=expression,
            motion=motion,
            parameters=parameters,
            duration=duration,
        )

    def _normalize_emotion(self, emotion: str) -> str:
        if not emotion:
            return "neutral"
        return self.EMOTION_ALIASES.get(emotion.lower(), "neutral")

    def _get_expression(self, emotion: str, intensity: str) -> str:
        profile = self.EMOTION_PROFILES.get(emotion, self.EMOTION_PROFILES["neutral"])
        return profile["expressions"].get(intensity, profile["expressions"]["medium"])

    def _get_motion(self, emotion: str, intensity: str) -> str:
        profile = self.EMOTION_PROFILES.get(emotion, self.EMOTION_PROFILES["neutral"])
        return profile["motions"].get(intensity, profile["motions"]["medium"])

    def _get_parameters(self, emotion: str, intensity: str, confidence: float) -> Dict[str, float]:
        profile = self.EMOTION_PROFILES.get(emotion, self.EMOTION_PROFILES["neutral"])
        base_params = profile["parameters"]
        intensity_multiplier = self.INTENSITY_MULTIPLIER.get(intensity, 1.0)

        # Keep low confidence outputs closer to neutral so the avatar doesn't overreact.
        confidence_multiplier = 0.55 + confidence * 0.45

        adjusted = {}
        for key, value in base_params.items():
            adjusted[key] = round(value * intensity_multiplier * confidence_multiplier, 4)

        return adjusted

    def get_action_for_text(self, text: str, emotion_result: EmotionAnalysisResult) -> Dict[str, Any]:
        action = self.map_emotion_to_action(emotion_result)
        normalized_emotion = self._normalize_emotion(emotion_result.emotion)

        return {
            "emotion": normalized_emotion,
            "intensity": emotion_result.intensity,
            "confidence": emotion_result.confidence,
            "expression": action.expression,
            "motion": action.motion,
            "parameters": action.parameters,
            "duration": action.duration,
            "text": text,
        }


_emotion_mapper = None


def get_emotion_mapper() -> EmotionActionMapper:
    global _emotion_mapper
    if _emotion_mapper is None:
        _emotion_mapper = EmotionActionMapper()
    return _emotion_mapper
