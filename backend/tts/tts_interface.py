"""
TTS (Text-to-Speech) Interface
Based on open-llm-vtuber's tts_interface.py
"""
from abc import ABC, abstractmethod
from typing import Union
import numpy as np


class TTSInterface(ABC):
    """Abstract interface for TTS systems"""
    
    @abstractmethod
    async def async_synthesize(self, text: str) -> Union[bytes, np.ndarray]:
        """Asynchronously synthesize text to audio"""
        pass
    
    @abstractmethod
    def synthesize(self, text: str) -> Union[bytes, np.ndarray]:
        """Synchronously synthesize text to audio"""
        pass
