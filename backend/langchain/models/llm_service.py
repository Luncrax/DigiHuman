"""
LangChain LLM service for DigiHuman.
"""
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.character_config import get_character_config
from backend.core.config import config
from backend.utils.logger import get_logger


logger = get_logger(__name__)


class LangChainLLMService:
    """LLM service class using LangChain ChatOpenAI."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful virtual assistant."),
        ])
        self.chain = self.prompt_template | self.llm | StrOutputParser()

        logger.info(f"LangChainLLMService initialized with model: {config.LLM_MODEL}")

    def _build_messages(self, message: str, history: List[Dict[str, Any]] = None):
        messages = []
        character_config = get_character_config()
        system_prompt = (
            character_config.llm_system_prompt.strip()
            if character_config.llm_system_prompt.strip()
            else "You are a helpful virtual assistant."
        )
        messages.append(SystemMessage(content=system_prompt))

        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))
        messages.append(HumanMessage(content=message))
        return messages

    async def generate_reply(self, message: str, history: List[Dict[str, Any]] = None) -> str:
        logger.info(f"Generating reply for message: {message}")
        messages = self._build_messages(message, history)

        try:
            reply = await self.llm.ainvoke(messages)
            filtered_reply = self._filter_response(reply.content)
            logger.info(f"Generated reply: {filtered_reply}")
            return filtered_reply
        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            return "抱歉，我在处理您的消息时遇到了问题。请稍后再试。"

    async def generate_reply_stream(self, message: str, history: List[Dict[str, Any]] = None):
        logger.info(f"Streaming reply for message: {message}")
        messages = self._build_messages(message, history)

        try:
            async for chunk in self.llm.astream(messages):
                content = getattr(chunk, "content", "")
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Error streaming reply: {e}")
            fallback = await self.generate_reply(message, history)
            if fallback:
                yield fallback

    async def generate_reply_with_context(self, message: str, context: Dict[str, Any] = None) -> str:
        logger.info(f"Generating reply with context for: {message}")

        messages = []
        if context and "system_prompt" in context:
            messages.append(SystemMessage(content=context["system_prompt"]))
        messages.append(HumanMessage(content=message))

        try:
            reply = await self.llm.ainvoke(messages)
            filtered_reply = self._filter_response(reply.content)
            logger.info(f"Generated contextual reply: {filtered_reply}")
            return filtered_reply
        except Exception as e:
            logger.error(f"Error generating contextual reply: {e}")
            return "抱歉，我在处理您的消息时遇到了问题。请稍后再试。"

    def _filter_response(self, response: str) -> str:
        import re

        filtered = re.sub(r"\[.*?思考.*?\]", "", response)
        filtered = re.sub(r"\(.*?思考.*?\)", "", filtered)
        filtered = re.sub(r"\{\{.*?思考.*?\}\}", "", filtered)
        filtered = filtered.strip()
        return filtered or "我理解您的意思。"

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": config.LLM_MODEL,
            "service": "LangChainLLMService",
            "temperature": config.LLM_TEMPERATURE,
            "max_tokens": config.LLM_MAX_TOKENS,
        }


llm_service = None


def get_llm_service() -> LangChainLLMService:
    global llm_service
    if llm_service is None:
        llm_service = LangChainLLMService()
    return llm_service


async def get_reply(message: str, history: List[Dict[str, Any]] = None) -> str:
    service = get_llm_service()
    return await service.generate_reply(message, history)
