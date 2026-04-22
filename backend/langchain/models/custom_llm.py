"""
Custom LLM service to handle non-OpenAI compatible API responses
"""
import json
from typing import Any, Dict, Optional, List, Iterator, Union
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from openai import AsyncOpenAI
from core.config import config
from utils.logger import get_logger


logger = get_logger(__name__)


class CustomChatLLM(BaseChatModel):
    """Custom ChatOpenAI that handles non-standard API responses"""

    @property
    def _llm_type(self) -> str:
        return "custom_chat_llm"

    def _get_chat_params(
        self,
        messages: List[BaseMessage],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Get parameters for chat completion"""
        # Convert LangChain messages to OpenAI format
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})

        params = {
            "model": config.LLM_MODEL,
            "messages": openai_messages,
            "temperature": config.LLM_TEMPERATURE,
            "max_tokens": config.LLM_MAX_TOKENS,
        }
        params.update(kwargs)
        return params

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Synchronous generation - not used for async operations"""
        raise NotImplementedError("Use async methods for this LLM")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generation"""
        # Create client for this request
        client = AsyncOpenAI(
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_API_KEY
        )

        params = self._get_chat_params(messages, **kwargs)

        try:
            logger.debug(f"Sending request to API: {params}")

            response = await client.chat.completions.create(**params)

            logger.debug(f"Raw API response: {response}")

            # Handle response based on its structure
            content = None
            if hasattr(response, 'choices') and response.choices and response.choices[0].message.content:
                # Standard OpenAI format
                content = response.choices[0].message.content
                logger.info(f"Standard format response: {content}")
            elif hasattr(response, 'body'):
                # Non-standard format with body field
                body = response.body
                if isinstance(body, str):
                    logger.info(f"Body format response: {body}")
                    content = body
                elif isinstance(body, dict) and 'content' in body:
                    logger.info(f"Body dict format response: {body['content']}")
                    content = body['content']
            elif hasattr(response, 'msg'):
                # Non-standard format with msg field
                logger.info(f"Msg format response: {response.msg}")
                content = response.msg

            # Fallback: try to extract content from any available field
            if content is None:
                if hasattr(response, 'dict'):
                    response_dict = response.dict()
                    for key in ['content', 'text', 'output', 'response']:
                        if key in response_dict and response_dict[key]:
                            logger.info(f"Fallback format response ({key}): {response_dict[key]}")
                            content = response_dict[key]
                            break

            # If nothing works, return raw response as string
            if content is None:
                response_str = str(response)
                logger.warning(f"Using raw response as fallback: {response_str}")
                content = response_str

            # Create ChatGeneration
            generation = ChatGeneration(message=AIMessage(content=content))
            return ChatResult(generations=[generation])

        except Exception as e:
            logger.error(f"Error in _agenerate: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return error message
            generation = ChatGeneration(message=AIMessage(content="抱歉，我在处理您的消息时遇到了问题。请稍后再试。"))
            return ChatResult(generations=[generation])

    async def achat(
        self,
        messages: List[BaseMessage],
        **kwargs: Any
    ) -> AIMessage:
        """Async chat completion with custom response parsing"""
        result = await self._agenerate(messages, **kwargs)
        if result.generations and len(result.generations) > 0:
            return result.generations[0].message
        return AIMessage(content="抱歉，我在处理您的消息时遇到了问题。请稍后再试。")

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model": config.LLM_MODEL,
            "temperature": config.LLM_TEMPERATURE,
            "max_tokens": config.LLM_MAX_TOKENS,
        }


# Singleton instance
_custom_llm = None


def get_custom_llm() -> CustomChatLLM:
    """Get or create custom LLM instance"""
    global _custom_llm
    if _custom_llm is None:
        _custom_llm = CustomChatLLM()
    return _custom_llm
