from __future__ import annotations

import hashlib
import math
import re


EMBEDDING_DIM = 128


def _tokenize(text: str) -> list[str]:
    normalized = (text or "").strip().lower()
    tokens = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_]+", normalized)
    if tokens:
        return tokens
    return [char for char in normalized if not char.isspace()]


class SimpleEmbeddingService:
    """
    Lightweight deterministic embedding for local prototyping.

    This is not a replacement for a semantic embedding model, but it lets us
    bootstrap Milvus integration and fall back locally when Milvus is offline.
    """

    dim: int = EMBEDDING_DIM

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = _tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for idx, byte in enumerate(digest):
                target_index = (idx * 17 + byte) % self.dim
                vector[target_index] += (byte / 255.0)

        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 0:
            return vector
        return [value / norm for value in vector]
