"""
Type definitions for the memory system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol


class MemorySource(str, Enum):
    """Source types for memory entries."""
    MEMORY = "memory"
    SESSIONS = "sessions"
    SKILLS = "skills"
    DOCS = "docs"


@dataclass(slots=True)
class MemoryChunk:
    """A chunk of text with metadata."""
    id: str
    text: str
    start_line: int
    end_line: int
    hash: str
    path: str
    source: str = "memory"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChunkRecord:
    """Database record for a chunk."""
    id: str
    path: str
    source: str
    start_line: int
    end_line: int
    hash: str
    model: str
    text: str
    embedding: Optional[List[float]] = None
    updated_at: int = 0


@dataclass(slots=True)
class SearchResult:
    """Search result from memory."""
    chunk_id: str
    path: str
    source: str
    text: str
    snippet: str
    score: float
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VectorSearchResult:
    """Vector search result."""
    chunk_id: str
    score: float
    embedding: Optional[List[float]] = None


@dataclass(slots=True)
class FTSSearchResult:
    """Full-text search result."""
    chunk_id: str
    score: float


@dataclass(slots=True)
class IndexResult:
    """Result of indexing a file."""
    file_path: str
    chunks_indexed: int
    chunks_skipped: int
    success: bool
    error: Optional[str] = None


@dataclass(slots=True)
class SyncResult:
    """Result of syncing memory files."""
    files_synced: int
    files_removed: int
    chunks_indexed: int
    errors: List[str] = field(default_factory=list)


@dataclass(slots=True)
class CompactResult:
    """Result of compacting short-term memory."""
    files_compacted: int
    files_archived: int
    summaries_generated: int


@dataclass(slots=True)
class MemoryStatus:
    """Status of the memory system."""
    initialized: bool
    files: int
    chunks: int
    vector_enabled: bool
    fts_enabled: bool
    watching: bool
    last_sync: Optional[datetime] = None


@dataclass(slots=True)
class MemoryStats:
    """Statistics of the memory system."""
    total_files: int
    total_chunks: int
    total_vectors: int
    cache_entries: int
    db_size_bytes: int
    avg_chunk_size: float


@dataclass(slots=True)
class ChunkConfig:
    """Configuration for chunking."""
    tokens: int = 400
    overlap: int = 80

    @property
    def max_chars(self) -> int:
        """Approximate max characters per chunk (1 token ≈ 4 chars)."""
        return self.tokens * 4

    @property
    def overlap_chars(self) -> int:
        """Approximate overlap characters."""
        return self.overlap * 4


@dataclass(slots=True)
class HybridConfig:
    """Configuration for hybrid search."""
    vector_weight: float = 0.7
    text_weight: float = 0.3
    candidate_multiplier: int = 2
    min_score: float = 0.5

    def __post_init__(self):
        # Normalize weights to sum to 1.0
        total = self.vector_weight + self.text_weight
        if total != 1.0 and total > 0:
            self.vector_weight /= total
            self.text_weight /= total


@dataclass(slots=True)
class CacheConfig:
    """Configuration for embedding cache."""
    enabled: bool = True
    max_entries: int = 10000


@dataclass(slots=True)
class SyncConfig:
    """Configuration for file syncing."""
    watch: bool = True
    watch_debounce_ms: int = 1000
    interval_minutes: int = 0
    on_search: bool = True


@dataclass(slots=True)
class ShortTermConfig:
    """Configuration for short-term memory."""
    enabled: bool = True
    retention_days: int = 7
    compaction_strategy: str = "summarize"  # "summarize" | "archive" | "delete"


@dataclass(slots=True)
class MemoryConfig:
    """Configuration for the memory system."""
    enabled: bool = True
    workspace_dir: str = "~/.bitwiseai"
    db_path: Optional[str] = None
    vector_enabled: bool = True
    vector_extension_path: Optional[str] = None
    chunking: ChunkConfig = field(default_factory=ChunkConfig)
    hybrid_search: HybridConfig = field(default_factory=HybridConfig)
    embedding_cache: CacheConfig = field(default_factory=CacheConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    short_term: ShortTermConfig = field(default_factory=ShortTermConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryConfig":
        """Create config from dictionary."""
        chunking_data = data.get("chunking", {})
        hybrid_data = data.get("hybrid_search", {})
        cache_data = data.get("embedding_cache", {})
        sync_data = data.get("sync", {})
        short_term_data = data.get("short_term", {})

        return cls(
            enabled=data.get("enabled", True),
            workspace_dir=data.get("workspace_dir", "~/.bitwiseai"),
            db_path=data.get("db_path"),
            vector_enabled=data.get("vector_enabled", True),
            vector_extension_path=data.get("vector_extension_path"),
            chunking=ChunkConfig(
                tokens=chunking_data.get("tokens", 400),
                overlap=chunking_data.get("overlap", 80)
            ),
            hybrid_search=HybridConfig(
                vector_weight=hybrid_data.get("vector_weight", 0.7),
                text_weight=hybrid_data.get("text_weight", 0.3),
                candidate_multiplier=hybrid_data.get("candidate_multiplier", 2),
                min_score=hybrid_data.get("min_score", 0.5)
            ),
            embedding_cache=CacheConfig(
                enabled=cache_data.get("enabled", True),
                max_entries=cache_data.get("max_entries", 10000)
            ),
            sync=SyncConfig(
                watch=sync_data.get("watch", True),
                watch_debounce_ms=sync_data.get("watch_debounce_ms", 1000),
                interval_minutes=sync_data.get("interval_minutes", 0),
                on_search=sync_data.get("on_search", True)
            ),
            short_term=ShortTermConfig(
                enabled=short_term_data.get("enabled", True),
                retention_days=short_term_data.get("retention_days", 7),
                compaction_strategy=short_term_data.get("compaction_strategy", "summarize")
            )
        )


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    @property
    def id(self) -> str:
        """Provider identifier."""
        ...

    @property
    def model(self) -> str:
        """Model name."""
        ...

    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        ...

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batch."""
        ...
