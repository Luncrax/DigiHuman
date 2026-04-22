"""
ASR (Automatic Speech Recognition) Interface
Based on open-llm-vtuber's asr_interface.py
"""
from abc import ABC, abstractmethod
from typing import Union
import numpy as np


class ASRInterface(ABC):
    """Abstract interface for ASR systems"""
    
    @abstractmethod
    async def async_transcribe(self, audio_input: Union[str, bytes]) -> str:
        """Asynchronously transcribe audio to text"""
        pass
    
    @abstractmethod
    async def async_transcribe_np(self, audio_array: np.ndarray) -> str:
        """Asynchronously transcribe numpy audio array to text"""
        pass
    
    @abstractmethod
    def transcribe(self, audio_input: Union[str, bytes]) -> str:
        """Synchronously transcribe audio to text"""
        pass
