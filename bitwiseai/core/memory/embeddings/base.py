"""
Base class for embedding providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Provider identifier."""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """Model name."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Number of dimensions in the embedding vectors."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    def get_provider_key(self) -> str:
        """
        Get a unique key for this provider configuration.
        Used for caching embeddings.
        """
        return f"{self.id}:{self.model}"


class EmbeddingError(Exception):
    """Error occurred during embedding."""
    pass


class EmbeddingRateLimitError(EmbeddingError):
    """Rate limit exceeded for embedding API."""
    pass


class EmbeddingAuthenticationError(EmbeddingError):
    """Authentication failed for embedding API."""
    pass
