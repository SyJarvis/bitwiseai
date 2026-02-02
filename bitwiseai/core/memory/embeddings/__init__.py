"""
Embedding providers for the memory system.
"""

from .base import (
    EmbeddingProvider,
    EmbeddingError,
    EmbeddingRateLimitError,
    EmbeddingAuthenticationError,
)

try:
    from .openai_provider import OpenAIEmbeddingProvider, ZhipuEmbeddingProvider
except ImportError:
    OpenAIEmbeddingProvider = None
    ZhipuEmbeddingProvider = None

__all__ = [
    "EmbeddingProvider",
    "EmbeddingError",
    "EmbeddingRateLimitError",
    "EmbeddingAuthenticationError",
    "OpenAIEmbeddingProvider",
    "ZhipuEmbeddingProvider",
]
