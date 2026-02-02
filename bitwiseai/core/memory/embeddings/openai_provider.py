"""
OpenAI embedding provider.
"""

import asyncio
from typing import List, Optional

try:
    from openai import AsyncOpenAI, APIError, RateLimitError, AuthenticationError
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from .base import EmbeddingProvider, EmbeddingError, EmbeddingRateLimitError, EmbeddingAuthenticationError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    # Model dimensions mapping
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "text-embedding-3-small",
        batch_size: int = 100,
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        """
        Initialize OpenAI embedding provider.

        Args:
            api_key: OpenAI API key
            base_url: Optional base URL for API (for custom endpoints)
            model: Model name to use
            batch_size: Maximum number of texts to embed in one batch
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
        """
        if not HAS_OPENAI:
            raise ImportError(
                "OpenAI package is required. "
                "Install it with: pip install openai"
            )

        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._timeout = timeout
        self._client: Optional[AsyncOpenAI] = None

    @property
    def id(self) -> str:
        """Provider identifier."""
        return "openai"

    @property
    def model(self) -> str:
        """Model name."""
        return self._model

    @property
    def dimensions(self) -> int:
        """Number of dimensions in the embedding vectors."""
        return self.MODEL_DIMENSIONS.get(self._model, 1536)

    def _get_client(self) -> AsyncOpenAI:
        """Get or create OpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
                max_retries=self._max_retries,
            )
        return self._client

    async def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimensions

        try:
            client = self._get_client()
            response = await client.embeddings.create(
                model=self._model,
                input=text.strip(),
            )
            return response.data[0].embedding
        except RateLimitError as e:
            raise EmbeddingRateLimitError(f"Rate limit exceeded: {e}") from e
        except AuthenticationError as e:
            raise EmbeddingAuthenticationError(f"Authentication failed: {e}") from e
        except APIError as e:
            raise EmbeddingError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise EmbeddingError(f"Failed to embed text: {e}") from e

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts in batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts and track their positions
        valid_texts = []
        empty_indices = []

        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text.strip())
            else:
                empty_indices.append(i)

        if not valid_texts:
            # All texts are empty
            return [[0.0] * self.dimensions for _ in texts]

        # Process in batches
        all_embeddings = []

        for i in range(0, len(valid_texts), self._batch_size):
            batch = valid_texts[i:i + self._batch_size]

            try:
                client = self._get_client()
                response = await client.embeddings.create(
                    model=self._model,
                    input=batch,
                )
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            except RateLimitError as e:
                raise EmbeddingRateLimitError(f"Rate limit exceeded: {e}") from e
            except AuthenticationError as e:
                raise EmbeddingAuthenticationError(f"Authentication failed: {e}") from e
            except APIError as e:
                raise EmbeddingError(f"OpenAI API error: {e}") from e
            except Exception as e:
                raise EmbeddingError(f"Failed to embed batch: {e}") from e

        # Insert zero vectors for empty texts
        result = []
        valid_idx = 0

        for i in range(len(texts)):
            if i in empty_indices:
                result.append([0.0] * self.dimensions)
            else:
                result.append(all_embeddings[valid_idx])
                valid_idx += 1

        return result


class ZhipuEmbeddingProvider(OpenAIEmbeddingProvider):
    """
    Zhipu AI embedding provider.
    Uses OpenAI-compatible API.
    """

    MODEL_DIMENSIONS = {
        "embedding-2": 1024,
        "embedding-3": 2048,
    }

    def __init__(
        self,
        api_key: str,
        model: str = "embedding-2",
        batch_size: int = 100,
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        """
        Initialize Zhipu embedding provider.

        Args:
            api_key: Zhipu API key
            model: Model name (embedding-2 or embedding-3)
            batch_size: Maximum number of texts to embed in one batch
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
        """
        super().__init__(
            api_key=api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4",
            model=model,
            batch_size=batch_size,
            max_retries=max_retries,
            timeout=timeout,
        )

    @property
    def id(self) -> str:
        """Provider identifier."""
        return "zhipu"
