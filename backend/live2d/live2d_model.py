"""
Live2D Model Handler
Based on open-llm-vtuber's live2d_model.py
"""
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Live2DModelConfig:
    """Configuration for Live2D model"""
    model_path: str
    motion_path: str
    expression_path: str
    physics_path: str
    pose_path: str


class Live2DModel:
    """Handles Live2D model operations"""
    
    def __init__(self, config: Live2DModelConfig):
        self.config = config
        self.model_data = None
        self.motion_data = None
        self.expression_data = None
        self.physics_data = None
        self.pose_data = None
        
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
                print(f"Motion file not found: {self.config.motion_path}")
            
            # Load expression data if available
            try:
                with open(self.config.expression_path, 'r', encoding='utf-8') as f:
                    self.expression_data = json.load(f)
            except FileNotFoundError:
                print(f"Expression file not found: {self.config.expression_path}")
            
            # Load physics data if available
            try:
                with open(self.config.physics_path, 'r', encoding='utf-8') as f:
                    self.physics_data = json.load(f)
            except FileNotFoundError:
                print(f"Physics file not found: {self.config.physics_path}")
            
            # Load pose data if available
            try:
                with open(self.config.pose_path, 'r', encoding='utf-8') as f:
                    self.pose_data = json.load(f)
            except FileNotFoundError:
                print(f"Pose file not found: {self.config.pose_path}")
                
        except Exception as e:
            print(f"Error loading Live2D model: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        if self.model_data:
            return {
                "model_path": self.config.model_path,
                "name": self.model_data.get("FileReferences", {}).get("Moc", "Unknown"),
                "has_motion": self.motion_data is not None,
                "has_expressions": self.expression_data is not None,
                "has_physics": self.physics_data is not None,
                "has_pose": self.pose_data is not None
            }
        return {}
    
    def update_expression(self, expression_name: str) -> bool:
        """Update model expression"""
        if self.expression_data:
            # Find the expression by name
            for expression in self.expression_data.get("expressions", []):
                if expression.get("Name") == expression_name:
                    # In a real implementation, this would update the model
                    print(f"Updating expression to: {expression_name}")
                    return True
        return False
    
    def update_motion(self, motion_name: str) -> bool:
        """Update model motion"""
        if self.motion_data:
            # Find the motion by name
            for motion_group in self.motion_data.get("groups", {}).values():
                for motion in motion_group:
                    if motion.get("File") == motion_name or motion.get("Name") == motion_name:
                        # In a real implementation, this would update the model
                        print(f"Updating motion to: {motion_name}")
                        return True
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
        # In a real implementation, this would update the Live2D model parameters
        print(f"Updating model parameters: {parameters}")
        return True
