from typing import Union, Dict, Any
from dataclasses import dataclass


@dataclass
class SentenceOutput:
    text: str
    is_final: bool = False


@dataclass
class DisplayText:
    text: str
    name: str = None
    avatar: str = None
