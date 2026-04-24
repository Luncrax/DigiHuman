"""
情感-动作映射模块
将情感分析结果映射到Live2D模型的表情和动作
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from backend.emotion.langchain_emotion_analyzer import EmotionAnalysisResult
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Live2DAction:
    """Live2D动作指令"""
    expression: str  # 表情名称
    motion: str  # 动作名称
    parameters: Dict[str, float]  # 模型参数
    duration: float  # 持续时间（秒）


class EmotionActionMapper:
    """情感到Live2D动作的映射器"""
    
    # 情感-表情映射表
    EMOTION_EXPRESSION_MAP = {
        "joy": {
            "low": "exp_01",  # 微笑
            "medium": "exp_02",  # 开心
            "high": "exp_02"  # 大笑
        },
        "sadness": {
            "low": "exp_03",  # 低落
            "medium": "exp_03",  # 难过
            "high": "exp_04"  # 哭泣
        },
        "anger": {
            "low": "exp_05",  # 严肃
            "medium": "exp_05",  # 生气
            "high": "exp_06"  # 愤怒
        },
        "surprise": {
            "low": "exp_07",  # 惊讶
            "medium": "exp_07",  # 震惊
            "high": "exp_08"  # 极度震惊
        },
        "fear": {
            "low": "exp_07",  # 紧张
            "medium": "exp_07",  # 害怕
            "high": "exp_08"  # 恐惧
        },
        "disgust": {
            "low": "exp_05",  # 嫌弃
            "medium": "exp_05",  # 厌恶
            "high": "exp_06"  # 极度厌恶
        },
        "neutral": {
            "low": "exp_01",  # 平静
            "medium": "exp_01",  # 自然
            "high": "exp_01"  # 放松
        }
    }
    
    # 情感-动作映射表
    EMOTION_MOTION_MAP = {
        "joy": {
            "low": "mtn_01",  # 挥手
            "medium": "mtn_01",  # 挥手
            "high": "special_01"  # 跳跃
        },
        "sadness": {
            "low": "mtn_03",  # 低头
            "medium": "mtn_03",  # 低头
            "high": "special_02"  # 抽泣
        },
        "anger": {
            "low": "mtn_02",  # 叉腰
            "medium": "mtn_02",  # 叉腰
            "high": "special_03"  # 跺脚
        },
        "surprise": {
            "low": "mtn_04",  # 后仰
            "medium": "mtn_04",  # 后仰
            "high": "special_01"  # 后退
        },
        "fear": {
            "low": "mtn_03",  # 蜷缩
            "medium": "mtn_03",  # 蜷缩
            "high": "special_02"  # 发抖
        },
        "disgust": {
            "low": "mtn_02",  # 摆手
            "medium": "mtn_02",  # 摆手
            "high": "mtn_04"  # 转身
        },
        "neutral": {
            "low": "mtn_01",  # idle
            "medium": "mtn_01",  # idle
            "high": "mtn_01"  # idle
        }
    }
    
    # 情感-参数映射表（用于微调模型参数）
    EMOTION_PARAMETER_MAP = {
        "joy": {
            "mouth_open": 0.3,
            "eye_l_open": 1.0,
            "eye_r_open": 1.0,
            "angle_x": 0.0,
            "angle_y": -0.2
        },
        "sadness": {
            "mouth_open": 0.0,
            "eye_l_open": 0.7,
            "eye_r_open": 0.7,
            "angle_x": 0.0,
            "angle_y": 0.3
        },
        "anger": {
            "mouth_open": 0.2,
            "eye_l_open": 1.0,
            "eye_r_open": 1.0,
            "angle_x": 0.0,
            "angle_y": 0.0
        },
        "surprise": {
            "mouth_open": 0.5,
            "eye_l_open": 1.0,
            "eye_r_open": 1.0,
            "angle_x": 0.0,
            "angle_y": -0.1
        },
        "fear": {
            "mouth_open": 0.3,
            "eye_l_open": 1.0,
            "eye_r_open": 1.0,
            "angle_x": 0.0,
            "angle_y": 0.1
        },
        "disgust": {
            "mouth_open": 0.1,
            "eye_l_open": 0.8,
            "eye_r_open": 0.8,
            "angle_x": 0.0,
            "angle_y": 0.0
        },
        "neutral": {
            "mouth_open": 0.0,
            "eye_l_open": 1.0,
            "eye_r_open": 1.0,
            "angle_x": 0.0,
            "angle_y": 0.0
        }
    }
    
    def __init__(self):
        """初始化映射器"""
        logger.info("EmotionActionMapper initialized")
    
    def map_emotion_to_action(self, emotion_result: EmotionAnalysisResult) -> Live2DAction:
        """
        将情感分析结果映射到Live2D动作
        
        Args:
            emotion_result: 情感分析结果
            
        Returns:
            Live2DAction: Live2D动作指令
        """
        emotion = emotion_result.emotion
        intensity = emotion_result.intensity
        confidence = emotion_result.confidence
        
        # 获取表情
        expression = self._get_expression(emotion, intensity)
        
        # 获取动作
        motion = self._get_motion(emotion, intensity)
        
        # 获取参数
        parameters = self._get_parameters(emotion, intensity, confidence)
        
        # 计算持续时间
        duration = self._get_duration(intensity)
        
        action = Live2DAction(
            expression=expression,
            motion=motion,
            parameters=parameters,
            duration=duration
        )
        
        logger.info(f"Mapped emotion {emotion} ({intensity}) to action: {expression}, {motion}")
        return action
    
    def _get_expression(self, emotion: str, intensity: str) -> str:
        """获取对应的表情"""
        emotion_map = self.EMOTION_EXPRESSION_MAP.get(emotion, self.EMOTION_EXPRESSION_MAP["neutral"])
        return emotion_map.get(intensity, emotion_map["medium"])
    
    def _get_motion(self, emotion: str, intensity: str) -> str:
        """获取对应的动作"""
        emotion_map = self.EMOTION_MOTION_MAP.get(emotion, self.EMOTION_MOTION_MAP["neutral"])
        return emotion_map.get(intensity, emotion_map["medium"])
    
    def _get_parameters(self, emotion: str, intensity: str, confidence: float) -> Dict[str, float]:
        """获取对应的模型参数"""
        base_params = self.EMOTION_PARAMETER_MAP.get(emotion, self.EMOTION_PARAMETER_MAP["neutral"]).copy()
        
        # 根据强度调整参数
        intensity_multiplier = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5
        }.get(intensity, 1.0)
        
        # 根据置信度微调
        confidence_factor = confidence
        
        # 调整参数值
        adjusted_params = {}
        for key, value in base_params.items():
            adjusted_params[key] = value * intensity_multiplier * confidence_factor
        
        return adjusted_params
    
    def _get_duration(self, intensity: str) -> float:
        """获取动作持续时间"""
        duration_map = {
            "low": 2.0,
            "medium": 3.0,
            "high": 4.0
        }
        return duration_map.get(intensity, 3.0)
    
    def get_action_for_text(self, text: str, emotion_result: EmotionAnalysisResult) -> Dict[str, Any]:
        """
        根据文本和情感结果获取完整的动作指令
        
        Args:
            text: 原始文本
            emotion_result: 情感分析结果
            
        Returns:
            Dict[str, Any]: 完整的动作指令字典
        """
        action = self.map_emotion_to_action(emotion_result)
        
        return {
            "emotion": emotion_result.emotion,
            "intensity": emotion_result.intensity,
            "confidence": emotion_result.confidence,
            "expression": action.expression,
            "motion": action.motion,
            "parameters": action.parameters,
            "duration": action.duration,
            "text": text
        }


# 全局映射器实例
_emotion_mapper = None


def get_emotion_mapper() -> EmotionActionMapper:
    """
    获取情感-动作映射器实例
    
    Returns:
        EmotionActionMapper: 映射器实例
    """
    global _emotion_mapper
    if _emotion_mapper is None:
        _emotion_mapper = EmotionActionMapper()
    return _emotion_mapper
