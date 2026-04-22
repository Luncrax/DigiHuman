"""
LangChain Conversation Chain for Virtual Human Assistant
Provides conversation handling using LangChain's chains and agents
"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from utils.logger import get_logger
from core.config import config
from ..models.custom_llm import get_custom_llm


# Initialize logger for this module
logger = get_logger(__name__)


class ConversationChain:
    """Conversation chain using LangChain"""
    
    def __init__(self):
        """Initialize the conversation chain"""
        # Initialize LLM with custom handler for non-OpenAI responses
        self.llm = get_custom_llm()

        # Create system prompt
        self.system_prompt = """
        You are a helpful virtual assistant.
        You should:
        1. Respond to user queries in a friendly and helpful manner
        2. Use the provided tools when necessary to get information
        3. Maintain context throughout the conversation
        4. Provide clear and concise answers
        """

        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}")
        ])

        # Create chain
        self.chain = self.prompt_template | self.llm | StrOutputParser()

        logger.info("ConversationChain initialized with custom LLM")
    
    async def run(self, input_text: str, history: List[Dict[str, Any]] = None) -> str:
        """
        Run the conversation chain

        Args:
            input_text (str): User input
            history (List[Dict[str, Any]]): Conversation history

        Returns:
            str: Generated response
        """
        logger.info(f"Running conversation chain with input: {input_text}")

        # Prepare messages
        messages = [SystemMessage(content=self.system_prompt)]

        # Add history messages
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # Add current input
        messages.append(HumanMessage(content=input_text))

        try:
            # Generate response using custom LLM
            response = await self.llm.achat(messages)

            logger.info(f"Generated response: {response.content}")
            return response.content
        except Exception as e:
            logger.error(f"Error running conversation chain: {e}")
            return "抱歉，我在处理您的消息时遇到了问题。请稍后再试。"
    
    async def run_with_tools(self, input_text: str, tools: List[Any], history: List[Dict[str, Any]] = None) -> str:
        """
        Run the conversation chain with tools
        
        Args:
            input_text (str): User input
            tools (List[Any]): List of tools to use
            history (List[Dict[str, Any]]): Conversation history
            
        Returns:
            str: Generated response
        """
        logger.info(f"Running conversation chain with tools for input: {input_text}")
        
        # For now, this is a placeholder
        # In a real implementation, we would use LangChain's agent with tools
        return await self.run(input_text, history)
