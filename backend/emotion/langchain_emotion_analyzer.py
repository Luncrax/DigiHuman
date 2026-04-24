"""
基于LangChain的情感分析模块
使用PydanticOutputParser实现结构化输出
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from backend.utils.logger import get_logger
from backend.core.config import config

logger = get_logger(__name__)


class EmotionAnalysisResult(BaseModel):
    """情感分析结果模型"""
    emotion: str = Field(
        description="主情感类型: joy(喜悦), sadness(悲伤), anger(愤怒), surprise(惊讶), fear(恐惧), disgust(厌恶), neutral(中性)",
        default="neutral"
    )
    confidence: float = Field(
        description="情感置信度，范围0.0-1.0",
        ge=0.0,
        le=1.0,
        default=0.5
    )
    details: Dict[str, float] = Field(
        description="各情感详细得分，包含joy、sadness、anger、surprise、fear、disgust、neutral的得分",
        default_factory=dict
    )
    intensity: str = Field(
        description="情感强度: low(低), medium(中), high(高)",
        default="medium"
    )


class LangChainEmotionAnalyzer:
    """基于LangChain的情感分析器"""
    
    # 有效的情感类型
    VALID_EMOTIONS = ["joy", "sadness", "anger", "surprise", "fear", "disgust", "neutral"]
    
    def __init__(self):
        """初始化情感分析器"""
        self.parser = PydanticOutputParser(pydantic_object=EmotionAnalysisResult)
        
        # 情感分析提示模板
        self.prompt_template = """分析以下文本的情感，返回结构化结果：

文本: {text}

请分析这段文本的情感，并返回JSON格式的结果：
- emotion: 主情感类型（joy/sadness/anger/surprise/fear/disgust/neutral）
- confidence: 置信度（0.0-1.0）
- details: 各情感得分，如{{"joy": 0.8, "sadness": 0.1, ...}}
- intensity: 情感强度（low/medium/high）

{format_instructions}
"""
        
        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        logger.info("LangChainEmotionAnalyzer initialized")
    
    async def analyze_emotion(self, text: str, llm_service=None) -> EmotionAnalysisResult:
        """
        分析文本情感
        
        Args:
            text: 待分析文本
            llm_service: LLM服务实例（可选，会使用默认服务）
            
        Returns:
            EmotionAnalysisResult: 情感分析结果
        """
        if not text or not text.strip():
            return EmotionAnalysisResult(
                emotion="neutral",
                confidence=1.0,
                details={emotion: 0.0 for emotion in self.VALID_EMOTIONS},
                intensity="low"
            )
        
        try:
            # 如果没有提供llm_service，使用默认的
            if llm_service is None:
                from backend.langchain.models.llm_service import get_llm_service
                llm_service = get_llm_service()
            
            # 构建提示
            prompt_text = self.prompt.format(text=text)
            
            # 调用LLM进行分析
            messages = [
                SystemMessage(content="你是一个情感分析专家。请分析用户文本的情感，返回结构化的JSON结果。"),
                HumanMessage(content=prompt_text)
            ]
            
            response = await llm_service.llm.ainvoke(messages)
            response_text = response.content
            
            # 解析结果
            try:
                result = self.parser.parse(response_text)
            except Exception as parse_error:
                logger.warning(f"Failed to parse emotion result: {parse_error}, using fallback")
                result = self._fallback_parse(response_text)
            
            # 验证情感类型
            if result.emotion not in self.VALID_EMOTIONS:
                result.emotion = "neutral"
            
            # 确保details包含所有情感类型
            for emotion in self.VALID_EMOTIONS:
                if emotion not in result.details:
                    result.details[emotion] = 0.0
            
            # 规范化置信度
            result.confidence = max(0.0, min(1.0, result.confidence))
            
            logger.info(f"Emotion analysis result: {result.emotion} (confidence: {result.confidence})")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing emotion: {e}")
            # 返回默认中性结果
            return EmotionAnalysisResult(
                emotion="neutral",
                confidence=0.5,
                details={emotion: 0.0 for emotion in self.VALID_EMOTIONS},
                intensity="low"
            )
    
    def _fallback_parse(self, text: str) -> EmotionAnalysisResult:
        """
        备用解析方法，当Pydantic解析失败时使用
        
        Args:
            text: LLM返回的文本
            
        Returns:
            EmotionAnalysisResult: 解析结果
        """
        import json
        import re
        
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[^}]*\}', text)
            if json_match:
                data = json.loads(json_match.group())
                return EmotionAnalysisResult(
                    emotion=data.get("emotion", "neutral"),
                    confidence=data.get("confidence", 0.5),
                    details=data.get("details", {}),
                    intensity=data.get("intensity", "medium")
                )
        except Exception:
            pass
        
        # 如果都失败，进行简单的关键词匹配
        text_lower = text.lower()
        emotion_scores = {}
        
        # 简单的关键词匹配
        keywords = {
            "joy": ["开心", "高兴", "快乐", "喜悦", "兴奋", "happy", "joy", "excited", "delighted"],
            "sadness": ["难过", "悲伤", "伤心", "沮丧", "sad", "sorrow", "depressed", "upset"],
            "anger": ["生气", "愤怒", "恼火", "angry", "mad", "furious", "annoyed"],
            "surprise": ["惊讶", "意外", "震惊", "surprised", "shocked", "amazed", "astonished"],
            "fear": ["害怕", "恐惧", "担心", "scared", "afraid", "fearful", "anxious"],
            "disgust": ["厌恶", "反感", "恶心", "disgusted", "repulsed", "revolted"]
        }
        
        for emotion, words in keywords.items():
            score = sum(1 for word in words if word in text_lower)
            emotion_scores[emotion] = min(1.0, score * 0.3)
        
        # 确定主情感
        if emotion_scores:
            main_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[main_emotion]
        else:
            main_emotion = "neutral"
            confidence = 0.5
        
        # 添加中性情感
        emotion_scores["neutral"] = 1.0 - confidence if confidence < 1.0 else 0.0
        
        # 确定强度
        if confidence > 0.7:
            intensity = "high"
        elif confidence > 0.4:
            intensity = "medium"
        else:
            intensity = "low"
        
        return EmotionAnalysisResult(
            emotion=main_emotion,
            confidence=confidence,
            details=emotion_scores,
            intensity=intensity
        )
    
    async def batch_analyze_emotion(self, texts: List[str], llm_service=None) -> List[EmotionAnalysisResult]:
        """
        批量分析多个文本的情感
        
        Args:
            texts: 文本列表
            llm_service: LLM服务实例
            
        Returns:
            List[EmotionAnalysisResult]: 情感分析结果列表
        """
        results = []
        for text in texts:
            result = await self.analyze_emotion(text, llm_service)
            results.append(result)
        return results


# 全局情感分析器实例
_emotion_analyzer = None


def get_emotion_analyzer() -> LangChainEmotionAnalyzer:
    """
    获取情感分析器实例
    
    Returns:
        LangChainEmotionAnalyzer: 情感分析器实例
    """
    global _emotion_analyzer
    if _emotion_analyzer is None:
        _emotion_analyzer = LangChainEmotionAnalyzer()
    return _emotion_analyzer


async def analyze_emotion(text: str, llm_service=None) -> EmotionAnalysisResult:
    """
    便捷函数：分析文本情感
    
    Args:
        text: 待分析文本
        llm_service: LLM服务实例
        
    Returns:
        EmotionAnalysisResult: 情感分析结果
    """
    analyzer = get_emotion_analyzer()
    return await analyzer.analyze_emotion(text, llm_service)
