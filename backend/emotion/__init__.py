"""
情感识别模块 - 提供文本情感分析功能
"""
from .langchain_emotion_analyzer import (
    LangChainEmotionAnalyzer,
    EmotionAnalysisResult,
    get_emotion_analyzer,
    analyze_emotion
)
from .emotion_controller import (
    EmotionController,
    EmotionControlResult,
    get_emotion_controller,
)

__all__ = [
    'LangChainEmotionAnalyzer',
    'EmotionAnalysisResult',
    'get_emotion_analyzer',
    'analyze_emotion',
    'EmotionController',
    'EmotionControlResult',
    'get_emotion_controller',
]
