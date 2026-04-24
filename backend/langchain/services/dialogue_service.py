"""
LangChain Dialogue Service for Virtual Human Assistant
Provides dialogue management using LangChain components
"""
from typing import Dict, Any, List
from loguru import logger
from ..models.llm_service import get_llm_service
from ..memory.memory_manager import get_memory_manager, clear_memory_manager
from ..chains.conversation_chain import ConversationChain
from ..tools.base_tools import get_tool_manager
from backend.utils.logger import get_logger


# Initialize logger for this module
logger = get_logger(__name__)


class LangChainDialogueService:
    """Dialogue service using LangChain components"""
    
    def __init__(self):
        """Initialize the dialogue service"""
        # Get instances of required services
        self.llm_service = get_llm_service()
        self.conversation_chain = ConversationChain()
        self.tool_manager = get_tool_manager()
        
        logger.info("LangChainDialogueService initialized")
    
    async def process_message(self, message: str, session_id: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message and generate a response
        
        Args:
            message (str): User message
            session_id (str): Session ID for memory management
            history (List[Dict[str, Any]]): Conversation history (optional)
            
        Returns:
            Dict[str, Any]: Response with generated text and updated history
        """
        logger.info(f"Processing message: {message} for session: {session_id}")
        
        # Get memory manager for the session
        memory_manager = get_memory_manager(session_id)
        
        # Load history if provided
        if history:
            memory_manager.load_memory_from_history(history)
        
        # Add user message to memory
        memory_manager.add_message("user", message)
        
        # Get current memory
        current_memory = memory_manager.get_memory()
        
        # Generate response using conversation chain
        response = await self.conversation_chain.run(message, current_memory)
        
        # Add assistant response to memory
        memory_manager.add_message("assistant", response)
        
        # Get updated memory
        updated_memory = memory_manager.get_memory()
        
        logger.info(f"Generated response: {response}")
        
        return {
            "response": response,
            "history": updated_memory
        }
    
    async def process_message_with_tools(self, message: str, session_id: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message with tools and generate a response
        
        Args:
            message (str): User message
            session_id (str): Session ID for memory management
            history (List[Dict[str, Any]]): Conversation history (optional)
            
        Returns:
            Dict[str, Any]: Response with generated text and updated history
        """
        logger.info(f"Processing message with tools: {message} for session: {session_id}")
        
        # Get memory manager for the session
        memory_manager = get_memory_manager(session_id)
        
        # Load history if provided
        if history:
            memory_manager.load_memory_from_history(history)
        
        # Add user message to memory
        memory_manager.add_message("user", message)
        
        # Get current memory
        current_memory = memory_manager.get_memory()
        
        # Get tools
        tools = self.tool_manager.get_tools()
        
        # Generate response using conversation chain with tools
        response = await self.conversation_chain.run_with_tools(message, tools, current_memory)
        
        # Add assistant response to memory
        memory_manager.add_message("assistant", response)
        
        # Get updated memory
        updated_memory = memory_manager.get_memory()
        
        logger.info(f"Generated response with tools: {response}")
        
        return {
            "response": response,
            "history": updated_memory
        }
    
    def clear_session(self, session_id: str):
        """
        Clear the session data
        
        Args:
            session_id (str): Session ID to clear
        """
        clear_memory_manager(session_id)
        logger.info(f"Cleared session: {session_id}")
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get session information
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Dict[str, Any]: Session information
        """
        memory_manager = get_memory_manager(session_id)
        memory_length = memory_manager.get_memory_length()
        
        return {
            "session_id": session_id,
            "memory_length": memory_length,
            "service": "LangChainDialogueService"
        }


# Global dialogue service instance
dialogue_service = None


def get_dialogue_service() -> LangChainDialogueService:
    """
    Get or create the dialogue service instance
    
    Returns:
        LangChainDialogueService: Dialogue service instance
    """
    global dialogue_service
    if dialogue_service is None:
        dialogue_service = LangChainDialogueService()
    return dialogue_service
