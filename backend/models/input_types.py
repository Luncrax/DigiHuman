from typing import List, Optional, Union, Dict, Any
from dataclasses import dataclass
from enum import Enum


class TextSource(Enum):
    INPUT = "input"
    CLIPBOARD = "clipboard"


@dataclass
class TextData:
    content: str
    source: TextSource


@dataclass
class ImageData:
    data: Union[str, bytes]  # Either base64 string or raw bytes


@dataclass
class BatchInputMetadata:
    skip_memory: bool = False


@dataclass
class BatchInput:
    texts: List[TextData]
    images: List[ImageData] = None
    metadata: Optional[BatchInputMetadata] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []
