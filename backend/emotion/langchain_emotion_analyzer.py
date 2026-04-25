"""
Emotion analysis with an LLM-first path plus a fast local fallback.
"""
import asyncio
from typing import Dict, List

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from backend.core.config import config
from backend.utils.logger import get_logger


logger = get_logger(__name__)


class EmotionAnalysisResult(BaseModel):
    emotion: str = Field(default="neutral")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    details: Dict[str, float] = Field(default_factory=dict)
    intensity: str = Field(default="medium")


class LangChainEmotionAnalyzer:
    VALID_EMOTIONS = ["joy", "sadness", "anger", "surprise", "fear", "disgust", "neutral", "shy"]

    KEYWORDS = {
        "joy": ["开心", "高兴", "快乐", "喜悦", "兴奋", "happy", "joy", "excited", "delighted", "哈哈", "！", "!"],
        "sadness": ["难过", "悲伤", "伤心", "沮丧", "sad", "sorrow", "depressed", "upset", "...", "……"],
        "anger": ["生气", "愤怒", "恼火", "angry", "mad", "furious", "annoyed"],
        "surprise": ["惊讶", "意外", "震惊", "surprised", "shocked", "amazed", "astonished", "?", "？"],
        "fear": ["害怕", "恐惧", "担心", "scared", "afraid", "fearful", "anxious", "紧张"],
        "disgust": ["厌恶", "反感", "恶心", "disgusted", "repulsed", "revolted"],
        "shy": ["害羞", "不好意思", "那个", "嗯", "shy", "bashful", "timid"],
    }

    def __init__(self):
        self.parser = PydanticOutputParser(pydantic_object=EmotionAnalysisResult)
        self.prompt_template = """分析以下文本的情绪，返回结构化结果：

文本: {text}

请返回 JSON：
- emotion: joy/sadness/anger/surprise/fear/disgust/neutral/shy
- confidence: 0.0-1.0
- details: 各情绪得分
- intensity: low/medium/high

{format_instructions}
"""
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        logger.info("LangChainEmotionAnalyzer initialized")

    def _normalize_result(self, result: EmotionAnalysisResult) -> EmotionAnalysisResult:
        if result.emotion not in self.VALID_EMOTIONS:
            result.emotion = "neutral"

        for emotion in self.VALID_EMOTIONS:
            result.details.setdefault(emotion, 0.0)

        result.confidence = max(0.0, min(1.0, float(result.confidence)))
        if result.intensity not in {"low", "medium", "high"}:
            result.intensity = "medium"
        return result

    def _heuristic_result(self, text: str) -> EmotionAnalysisResult:
        text_lower = (text or "").lower()
        scores = {emotion: 0.0 for emotion in self.VALID_EMOTIONS}

        for emotion, words in self.KEYWORDS.items():
            score = sum(1 for word in words if word in text_lower)
            scores[emotion] = min(1.0, score * 0.26)

        main_emotion = max(scores, key=scores.get)
        confidence = scores[main_emotion]

        if confidence <= 0:
            main_emotion = "neutral"
            confidence = 0.55
            scores["neutral"] = 0.55
        else:
            scores["neutral"] = max(scores["neutral"], max(0.0, 1.0 - confidence))

        if confidence > 0.72:
            intensity = "high"
        elif confidence > 0.42:
            intensity = "medium"
        else:
            intensity = "low"

        return EmotionAnalysisResult(
            emotion=main_emotion,
            confidence=confidence,
            details=scores,
            intensity=intensity,
        )

    async def analyze_emotion(self, text: str, llm_service=None) -> EmotionAnalysisResult:
        if not text or not text.strip():
            return EmotionAnalysisResult(
                emotion="neutral",
                confidence=1.0,
                details={emotion: 0.0 for emotion in self.VALID_EMOTIONS},
                intensity="low",
            )

        if llm_service is None:
            from backend.langchain.models.llm_service import get_llm_service
            llm_service = get_llm_service()

        prompt_text = self.prompt.format(text=text)
        messages = [
            SystemMessage(content="你是一个情绪分析专家，请仅返回结构化 JSON 结果。"),
            HumanMessage(content=prompt_text),
        ]

        try:
            response = await asyncio.wait_for(
                llm_service.llm.ainvoke(messages),
                timeout=max(0.2, float(config.EMOTION_ANALYSIS_TIMEOUT)),
            )
            response_text = response.content

            try:
                result = self.parser.parse(response_text)
            except Exception as parse_error:
                logger.warning("Failed to parse emotion result, using heuristic fallback: %s", parse_error)
                result = self._heuristic_result(text)

            normalized = self._normalize_result(result)
            logger.info("Emotion analysis result: %s (confidence: %.2f)", normalized.emotion, normalized.confidence)
            return normalized
        except Exception as exc:
            logger.warning("Emotion analysis fallback triggered: %s", exc)
            return self._heuristic_result(text)

    async def batch_analyze_emotion(self, texts: List[str], llm_service=None) -> List[EmotionAnalysisResult]:
        results = []
        for text in texts:
            results.append(await self.analyze_emotion(text, llm_service))
        return results


_emotion_analyzer = None


def get_emotion_analyzer() -> LangChainEmotionAnalyzer:
    global _emotion_analyzer
    if _emotion_analyzer is None:
        _emotion_analyzer = LangChainEmotionAnalyzer()
    return _emotion_analyzer


async def analyze_emotion(text: str, llm_service=None) -> EmotionAnalysisResult:
    analyzer = get_emotion_analyzer()
    return await analyzer.analyze_emotion(text, llm_service)
