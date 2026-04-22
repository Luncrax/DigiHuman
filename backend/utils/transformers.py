"""
Transformer functions for text processing
"""
import re
from typing import Any, Dict, List, Union, Callable, Awaitable
from ..models.output_types import SentenceOutput, DisplayText


def sentence_divider(
    faster_first_response: bool = True,
    segment_method: str = "pysbd",
    valid_tags: List[str] = None
):
    """
    Decorator to divide text into sentences
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async for output in func(*args, **kwargs):
                if isinstance(output, str):
                    # Simple sentence splitting
                    sentences = re.split(r'[.!?。！？]+', output)
                    sentences = [s.strip() for s in sentences if s.strip()]
                    for sentence in sentences:
                        if sentence:
                            yield SentenceOutput(text=sentence, is_final=False)
                else:
                    yield output
        return wrapper
    return decorator


def actions_extractor(live2d_model: Any = None):
    """
    Decorator to extract actions from text
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async for output in func(*args, **kwargs):
                yield output
        return wrapper
    return decorator


def tts_filter(tts_preprocessor_config: Any = None):
    """
    Decorator to filter text for TTS
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async for output in func(*args, **kwargs):
                yield output
        return wrapper
    return decorator


def display_processor():
    """
    Decorator to process display text
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async for output in func(*args, **kwargs):
                if isinstance(output, str):
                    yield DisplayText(text=output)
                else:
                    yield output
        return wrapper
    return decorator
