"""
LangChain Memory Manager for Virtual Human Assistant
Provides memory management using LangChain's memory components
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from backend.utils.logger import get_logger
from backend.history_manager import get_history, store_message as store_history_message


# Initialize logger for this module
logger = get_logger(__name__)


class LangChainMemoryManager:
    """Memory manager using LangChain's InMemoryChatMessageHistory with persistence"""
    
    def __init__(self, session_id: str = None):
        """
        Initialize the memory manager
        
        Args:
            session_id (str): Session ID for memory management
        """
        self.session_id = session_id or f"session_{id(self)}"
        # Initialize LangChain memory
        self.memory = InMemoryChatMessageHistory()
        # Initialize memory file path for persistence
        self.memory_dir = os.path.join("chat_memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.memory_file = os.path.join(self.memory_dir, f"{self.session_id}.json")
        # Load memory from file if it exists
        self.load_memory_from_file()
        logger.info(f"LangChainMemoryManager initialized for session: {self.session_id}")
    
    def add_message(self, role: str, content: str):
        """
        Add a message to the conversation memory
        
        Args:
            role (str): Role of the message (user, assistant, system)
            content (str): Content of the message
        """
        # Add message to LangChain memory
        if role == "user":
            self.memory.add_message(HumanMessage(content=content))
        elif role == "assistant":
            self.memory.add_message(AIMessage(content=content))
        elif role == "system":
            self.memory.add_message(SystemMessage(content=content))
        logger.debug(f"Added message to LangChain memory: {role} - {content[:50]}...")
        # Save memory to file
        self.save_memory_to_file()
    
    def get_memory(self) -> List[Dict[str, str]]:
        """
        Get the current conversation memory
        
        Returns:
            List[Dict[str, str]]: Conversation memory as list of messages
        """
        # Convert LangChain messages to dict format
        memory = []
        for msg in self.memory.messages:
            if isinstance(msg, HumanMessage):
                memory.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                memory.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, SystemMessage):
                memory.append({"role": "system", "content": msg.content})
        return memory
    
    def get_memory_as_messages(self):
        """
        Get the current conversation memory as LangChain message objects
        
        Returns:
            List[BaseMessage]: Conversation memory as LangChain message objects
        """
        return self.memory.messages
    
    def clear_memory(self):
        """
        Clear the conversation memory
        """
        # Clear LangChain memory
        self.memory.clear()
        # Clear memory file
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
        logger.info(f"Memory cleared for session: {self.session_id}")
    
    def get_memory_length(self) -> int:
        """
        Get the length of the conversation memory
        
        Returns:
            int: Number of messages in memory
        """
        return len(self.memory.messages)
    
    def load_memory_from_history(self, history: List[Dict[str, str]]):
        """
        Load memory from a list of messages
        
        Args:
            history (List[Dict[str, str]]): List of messages to load
        """
        # Clear existing memory
        self.clear_memory()
        
        # Load messages from history
        for msg in history:
            role = msg.get("role")
            content = msg.get("content")
            if role and content:
                self.add_message(role, content)
        
        logger.info(f"Loaded {len(history)} messages from history")
    
    def save_memory_to_file(self):
        """
        Save memory to file for persistence
        """
        try:
            memory_data = self.get_memory()
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Memory saved to file: {self.memory_file}")
        except Exception as e:
            logger.error(f"Failed to save memory to file: {e}")
    
    def load_memory_from_file(self):
        """
        Load memory from file
        """
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    memory_data = json.load(f)
                self.load_memory_from_history(memory_data)
                logger.debug(f"Memory loaded from file: {self.memory_file}")
        except Exception as e:
            logger.error(f"Failed to load memory from file: {e}")
    
    def save_to_history_manager(self, history_uid: str):
        """
        Save current memory to history manager
        
        Args:
            history_uid (str): History unique identifier
        """
        try:
            memory_data = self.get_memory()
            for msg in memory_data:
                role = msg.get("role")
                content = msg.get("content")
                if role and content:
                    # Map LangChain roles to history manager roles
                    history_role = "human" if role == "user" else "ai" if role == "assistant" else role
                    store_history_message(self.session_id, history_uid, history_role, content)
            logger.info(f"Memory saved to history manager for session: {self.session_id}, history: {history_uid}")
        except Exception as e:
            logger.error(f"Failed to save memory to history manager: {e}")
    
    def load_from_history_manager(self, history_uid: str):
        """
        Load memory from history manager
        
        Args:
            history_uid (str): History unique identifier
        """
        try:
            history_messages = get_history(self.session_id, history_uid)
            # Convert history messages to LangChain format
            langchain_history = []
            for msg in history_messages:
                role = msg.get("role")
                content = msg.get("content")
                if role and content:
                    # Map history roles to LangChain roles
                    langchain_role = "user" if role == "human" else "assistant" if role == "ai" else role
                    langchain_history.append({"role": langchain_role, "content": content})
            self.load_memory_from_history(langchain_history)
            logger.info(f"Memory loaded from history manager for session: {self.session_id}, history: {history_uid}")
        except Exception as e:
            logger.error(f"Failed to load memory from history manager: {e}")


# Memory manager registry to store memory instances per session
memory_registry = {}


def get_memory_manager(session_id: str) -> LangChainMemoryManager:
    """
    Get or create a memory manager for a session
    
    Args:
        session_id (str): Session ID
        
    Returns:
        LangChainMemoryManager: Memory manager instance
    """
    if session_id not in memory_registry:
        memory_registry[session_id] = LangChainMemoryManager(session_id)
    return memory_registry[session_id]


def clear_memory_manager(session_id: str):
    """
    Clear and remove a memory manager for a session
    
    Args:
        session_id (str): Session ID
    """
    if session_id in memory_registry:
        memory_registry[session_id].clear_memory()
        del memory_registry[session_id]
        logger.info(f"Memory manager cleared and removed for session: {session_id}")


def list_sessions() -> List[str]:
    """
    List all sessions with memory
    
    Returns:
        List[str]: List of session IDs
    """
    session_ids = []
    memory_dir = os.path.join("chat_memory")
    if os.path.exists(memory_dir):
        for filename in os.listdir(memory_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]
                session_ids.append(session_id)
    return session_ids


def export_session(session_id: str) -> Dict[str, Any]:
    """
    Export session memory
    
    Args:
        session_id (str): Session ID
        
    Returns:
        Dict[str, Any]: Session memory data
    """
    memory_manager = get_memory_manager(session_id)
    return {
        "session_id": session_id,
        "messages": memory_manager.get_memory(),
        "exported_at": datetime.now().isoformat()
    }


def import_session(session_id: str, data: Dict[str, Any]):
    """
    Import session memory
    
    Args:
        session_id (str): Session ID
        data (Dict[str, Any]): Session memory data
    """
    memory_manager = get_memory_manager(session_id)
    messages = data.get("messages", [])
    memory_manager.load_memory_from_history(messages)
    logger.info(f"Session memory imported for session: {session_id}")
