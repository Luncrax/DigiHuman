"""
LLM Service module for Virtual Human Assistant
Provides language model functionality for generating replies using LangChain
"""
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from backend.utils.logger import get_logger
from backend.core.config import config


# Initialize logger for this module
logger = get_logger(__name__)


class LLMService:
    def __init__(self):
        # Use LangChain's ChatOpenAI for model interaction
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS
        )
        
        # Create a simple prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful virtual assistant.")
        ])
        
        # Create a chain for generating responses
        self.chain = self.prompt_template | self.llm | StrOutputParser()
        
    async def generate_reply(self, message: str, history: List[Dict[str, Any]] = None) -> str:
        """
        Generate a reply to the given message using the LLM
        
        Args:
            message (str): Input message to generate reply for
            history (List[Dict[str, Any]]): Conversation history with role and content
            
        Returns:
            str: Generated reply from the LLM
        """
        logger.info(f"Generating reply for message: {message}")
        
        # Convert history to LangChain message objects
        messages = []
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))
        
        # Add the current user message
        messages.append(HumanMessage(content=message))
        
        try:
            # Use LangChain to generate response
            reply = await self.llm.ainvoke(messages)
            
            logger.info(f"Generated reply: {reply.content}")
            return reply.content
        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            # Fallback response in case of error
            return "抱歉，我在处理您的消息时遇到了问题。请稍后再试。"
    
    async def generate_reply_with_context(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Generate a reply with additional context information
        
        Args:
            message (str): Input message to generate reply for
            context (Dict[str, Any]): Additional context information
            
        Returns:
            str: Generated reply from the LLM
        """
        logger.info(f"Generating reply with context for: {message}")
        
        # Prepare messages with system context if provided
        messages = []
        if context and "system_prompt" in context:
            messages.append(SystemMessage(content=context["system_prompt"]))
        
        # Add the current user message
        messages.append(HumanMessage(content=message))
        
        try:
            # Use LangChain to generate response
            reply = await self.llm.ainvoke(messages)
            
            logger.info(f"Generated contextual reply: {reply.content}")
            return reply.content
        except Exception as e:
            logger.error(f"Error generating contextual reply: {e}")
            # Fallback response in case of error
            return "抱歉，我在处理您的消息时遇到了问题。请稍后再试。"


# Global instance of LLMService will be created later to avoid initialization issues
llm_service = None


def get_llm_service():
    """Get or create the LLM service instance."""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service


async def get_reply(message: str, history: List[Dict[str, Any]] = None) -> str:
    """
    Convenience function to get a reply from the LLM
    
    Args:
        message (str): Input message to generate reply for
        history (List[Dict[str, Any]]): Conversation history
        
    Returns:
        str: Generated reply from the LLM
    """
    service = get_llm_service()
    return await service.generate_reply(message, history)
