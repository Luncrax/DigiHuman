"""
Service Context Manager for DigiHuman
========================
This module contains the ServiceContext class that manages all the services
for a connected client, similar to open-llm-vtuber's service_context.py
"""

import json
from typing import Callable, Optional
from loguru import logger
from fastapi import WebSocket

from backend.live2d.live2d_model import Live2DModel
from backend.asr.asr_interface import ASRInterface
from backend.tts.tts_interface import TTSInterface


class ContextManager:
    """Context manager for WebSocket connections"""
    
    def __init__(self):
        self.history_uid: Optional[str] = None

    async def initialize_context(self, client_uid: str):
        """Initialize context for a client"""
        logger.info(f"Initializing context for client: {client_uid}")
        self.history_uid = None  # Initialize with no history

    async def cleanup_context(self, client_uid: str):
        """Clean up context for a client"""
        logger.info(f"Cleaning up context for client: {client_uid}")
        self.history_uid = None  # Clear history reference


class ServiceContext:
    """Initializes, stores, and updates the asr, tts, and llm instances and other
    configurations for a connected client."""

    def __init__(self):
        self.live2d_model: Optional[Live2DModel] = None
        self.asr_engine: Optional[ASRInterface] = None
        self.tts_engine: Optional[TTSInterface] = None

        # Store the system prompt
        self.system_prompt: str = ""

        self.send_text: Optional[Callable] = None
        self.client_uid: str = ""

    def __str__(self):
        return (
            f"ServiceContext:\n"
            f"  Live2D Model: {self.live2d_model.model_info if self.live2d_model else 'Not Loaded'}\n"
            f"  ASR Engine: {type(self.asr_engine).__name__ if self.asr_engine else 'Not Loaded'}\n"
            f"  TTS Engine: {type(self.tts_engine).__name__ if self.tts_engine else 'Not Loaded'}\n"
            f"  System Prompt: {self.system_prompt or 'Not Set'}"
        )

    async def load_services(
        self,
        live2d_model: Live2DModel,
        asr_engine: ASRInterface,
        tts_engine: TTSInterface,
        system_prompt: str = "",
        send_text: Optional[Callable] = None,
        client_uid: str = "",
    ) -> None:
        """
        Load the ServiceContext with the provided service instances.
        """
        self.live2d_model = live2d_model
        self.asr_engine = asr_engine
        self.tts_engine = tts_engine
        self.system_prompt = system_prompt
        self.send_text = send_text
        self.client_uid = client_uid

        logger.debug(f"Loaded service context for client: {client_uid}")

    async def close(self):
        """Clean up resources."""
        logger.info("Closing ServiceContext resources...")
        logger.info("ServiceContext closed.")
