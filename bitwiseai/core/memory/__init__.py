"""
Memory system for BitwiseAI.

Provides a dual-layer memory system with:
- Short-term memory: daily log files
- Long-term memory: curated persistent storage
- Hybrid search: vector similarity + BM25 keyword search
- File watching: automatic reindexing on changes
"""

from .embeddings import (
    EmbeddingProvider,
    EmbeddingError,
    EmbeddingRateLimitError,
    EmbeddingAuthenticationError,
    OpenAIEmbeddingProvider,
    ZhipuEmbeddingProvider,
)
from .manager import MemoryManager
from .types import (
    ChunkConfig,
    CompactResult,
    HybridConfig,
    IndexResult,
    MemoryChunk,
    MemoryConfig,
    MemorySource,
    MemoryStats,
    MemoryStatus,
    SearchResult,
    SyncResult,
)

__all__ = [
    # Core classes
    "MemoryManager",
    # Embedding providers
    "EmbeddingProvider",
    "EmbeddingError",
    "EmbeddingRateLimitError",
    "EmbeddingAuthenticationError",
    "OpenAIEmbeddingProvider",
    "ZhipuEmbeddingProvider",
    # Types
    "ChunkConfig",
    "CompactResult",
    "HybridConfig",
    "IndexResult",
    "MemoryChunk",
    "MemoryConfig",
    "MemorySource",
    "MemoryStats",
    "MemoryStatus",
    "SearchResult",
    "SyncResult",
]

__version__ = "1.0.0"
