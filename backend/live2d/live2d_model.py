"""
Live2D Model Handler
Based on open-llm-vtuber's live2d_model.py
"""
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from backend.emotion.langchain_emotion_analyzer import EmotionAnalysisResult
from backend.live2d.emotion_mapper import get_emotion_mapper, Live2DAction
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Live2DModelConfig:
    """Configuration for Live2D model"""
    model_path: str
    motion_path: str
    expression_path: str
    physics_path: str
    pose_path: str


@dataclass
class MotionQueueItem:
    """动作队列项"""
    motion_name: str
    expression_name: str
    parameters: Dict[str, float]
    priority: int
    duration: float


class Live2DModel:
    """Handles Live2D model operations"""
    
    def __init__(self, config: Live2DModelConfig):
        self.config = config
        self.model_data = None
        self.motion_data = None
        self.expression_data = None
        self.physics_data = None
        self.pose_data = None
        
        # 动作队列管理
        self.motion_queue: List[MotionQueueItem] = []
        self.current_motion: Optional[MotionQueueItem] = None
        
        # 当前状态
        self.current_expression = "exp_01"
        self.current_parameters = self.get_default_parameters()
        
        # 情感映射器
        self.emotion_mapper = get_emotion_mapper()
        
        # Load model data
        self.load_model()
    
    def load_model(self):
        """Load Live2D model data"""
        try:
            # Load model JSON
            with open(self.config.model_path, 'r', encoding='utf-8') as f:
                self.model_data = json.load(f)
            
            # Load motion data if available
            try:
                with open(self.config.motion_path, 'r', encoding='utf-8') as f:
                    self.motion_data = json.load(f)
            except FileNotFoundError:
                logger.warning(f"Motion file not found: {self.config.motion_path}")
            
            # Load expression data if available
            try:
                with open(self.config.expression_path, 'r', encoding='utf-8') as f:
                    self.expression_data = json.load(f)
            except FileNotFoundError:
                logger.warning(f"Expression file not found: {self.config.expression_path}")
            
            # Load physics data if available
            try:
                with open(self.config.physics_path, 'r', encoding='utf-8') as f:
                    self.physics_data = json.load(f)
            except FileNotFoundError:
                logger.warning(f"Physics file not found: {self.config.physics_path}")
            
            # Load pose data if available
            try:
                with open(self.config.pose_path, 'r', encoding='utf-8') as f:
                    self.pose_data = json.load(f)
            except FileNotFoundError:
                logger.warning(f"Pose file not found: {self.config.pose_path}")
                
        except Exception as e:
            logger.error(f"Error loading Live2D model: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        if self.model_data:
            return {
                "model_path": self.config.model_path,
                "name": self.model_data.get("FileReferences", {}).get("Moc", "Unknown"),
                "has_motion": self.motion_data is not None,
                "has_expressions": self.expression_data is not None,
                "has_physics": self.physics_data is not None,
                "has_pose": self.pose_data is not None,
                "current_expression": self.current_expression,
                "current_parameters": self.current_parameters
            }
        return {}
    
    def update_expression(self, expression_name: str) -> bool:
        """Update model expression"""
        try:
            if self.expression_data:
                # Find the expression by name
                for expression in self.expression_data.get("expressions", []):
                    if expression.get("Name") == expression_name:
                        self.current_expression = expression_name
                        logger.info(f"Updating expression to: {expression_name}")
                        return True
            
            # 如果找不到指定表情，使用默认表情
            logger.warning(f"Expression not found: {expression_name}, using default")
            self.current_expression = "exp_01"
            return True
            
        except Exception as e:
            logger.error(f"Error updating expression: {e}")
            return False
    
    def update_motion(self, motion_name: str) -> bool:
        """Update model motion"""
        try:
            if self.motion_data:
                # Find the motion by name
                for motion_group in self.motion_data.get("groups", {}).values():
                    for motion in motion_group:
                        if motion.get("File") == motion_name or motion.get("Name") == motion_name:
                            logger.info(f"Updating motion to: {motion_name}")
                            return True
            
            logger.warning(f"Motion not found: {motion_name}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating motion: {e}")
            return False
    
    def get_default_parameters(self) -> Dict[str, float]:
        """Get default model parameters"""
        return {
            "angle_x": 0.0,
            "angle_y": 0.0,
            "angle_z": 0.0,
            "eye_l_open": 1.0,
            "eye_r_open": 1.0,
            "eye_ball_x": 0.0,
            "eye_ball_y": 0.0,
            "mouth_open": 0.0,
            "breath": 0.0
        }
    
    def update_parameters(self, parameters: Dict[str, float]) -> bool:
        """Update model parameters"""
        try:
            # 合并参数，保留默认值
            for key, value in parameters.items():
                if key in self.current_parameters:
                    # 平滑过渡（简单实现）
                    self.current_parameters[key] = value
            
            logger.info(f"Updating model parameters: {parameters}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating parameters: {e}")
            return False
    
    # ==================== 情感响应方法 ====================
    
    def control_live2d_by_emotion(self, emotion_result: EmotionAnalysisResult) -> bool:
        """
        根据情感分析结果控制Live2D模型
        
        Args:
            emotion_result: 情感分析结果
            
        Returns:
            bool: 是否执行成功
        """
        try:
            # 使用情感映射器获取动作指令
            action = self.emotion_mapper.map_emotion_to_action(emotion_result)
            
            # 设置表情
            self.set_live2d_expression(action.expression)
            
            # 播放动作
            self.play_live2d_motion(action.motion, priority=1)
            
            # 更新参数
            self.update_parameters(action.parameters)
            
            logger.info(f"Controlled Live2D by emotion: {emotion_result.emotion}")
            return True
            
        except Exception as e:
            logger.error(f"Error controlling Live2D by emotion: {e}")
            return False
    
    def set_live2d_expression(self, expression_name: str) -> bool:
        """
        设置Live2D模型的表情
        
        Args:
            expression_name: 表情名称
            
        Returns:
            bool: 是否设置成功
        """
        return self.update_expression(expression_name)
    
    def play_live2d_motion(self, motion_name: str, priority: int = 1) -> bool:
        """
        播放Live2D模型的动作
        
        Args:
            motion_name: 动作名称
            priority: 优先级（1-10，数字越大优先级越高）
            
        Returns:
            bool: 是否播放成功
        """
        try:
            # 添加到动作队列
            queue_item = MotionQueueItem(
                motion_name=motion_name,
                expression_name=self.current_expression,
                parameters=self.current_parameters.copy(),
                priority=priority,
                duration=3.0  # 默认持续时间
            )
            
            # 根据优先级插入队列
            inserted = False
            for i, item in enumerate(self.motion_queue):
                if priority > item.priority:
                    self.motion_queue.insert(i, queue_item)
                    inserted = True
                    break
            
            if not inserted:
                self.motion_queue.append(queue_item)
            
            # 执行动作
            self.update_motion(motion_name)
            
            logger.info(f"Playing motion: {motion_name} (priority: {priority})")
            return True
            
        except Exception as e:
            logger.error(f"Error playing motion: {e}")
            return False
    
    def get_emotion_control_command(self, emotion_result: EmotionAnalysisResult) -> Dict[str, Any]:
        """
        获取情感控制指令（用于发送到前端）
        
        Args:
            emotion_result: 情感分析结果
            
        Returns:
            Dict[str, Any]: 控制指令字典
        """
        return self.emotion_mapper.get_action_for_text("", emotion_result)
    
    def reset_to_neutral(self) -> bool:
        """
        重置为中性状态
        
        Returns:
            bool: 是否重置成功
        """
        try:
            self.current_expression = "exp_01"
            self.current_parameters = self.get_default_parameters()
            self.motion_queue.clear()
            
            logger.info("Reset Live2D to neutral state")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting to neutral: {e}")
            return False
