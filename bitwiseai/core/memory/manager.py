"""
Memory manager - unified interface for the dual-layer memory system.
"""

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .indexer import MemoryIndexer
from .searcher import MemorySearcher
from .storage import SQLiteStorage
from .types import (
    ChunkConfig,
    CompactResult,
    EmbeddingProvider,
    HybridConfig,
    IndexResult,
    MemoryConfig,
    MemorySource,
    MemoryStats,
    MemoryStatus,
    SearchResult,
    SyncResult,
)
from .watcher import create_file_watcher


class MemoryManager:
    """
    Unified memory manager - dual-layer memory system.
    - Short-term: memory/YYYY-MM-DD.md daily log files
    - Long-term: MEMORY.md curated persistent memory
    """

    def __init__(
        self,
        workspace_dir: str = "~/.bitwiseai",
        db_path: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        config: Optional[MemoryConfig] = None
    ):
        """
        Initialize memory manager.

        Args:
            workspace_dir: Workspace directory
            db_path: Database path (default: workspace_dir/memory.db)
            embedding_provider: Embedding provider
            config: Memory system configuration
        """
        self.config = config or MemoryConfig()
        self.workspace_dir = Path(workspace_dir).expanduser()

        # Ensure workspace directory exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Memory directories
        self.memory_dir = self.workspace_dir / "memory"
        self.memory_file = self.workspace_dir / "MEMORY.md"

        # Create memory directory
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # Initialize storage
        db_path = db_path or str(self.workspace_dir / "memory.db")
        self.storage = SQLiteStorage(
            db_path=db_path,
            vector_enabled=self.config.vector_enabled,
            vector_extension_path=self.config.vector_extension_path
        )

        # Initialize embedding provider
        self.embedding = embedding_provider

        # Initialize indexer and searcher (will be created in initialize())
        self.indexer: Optional[MemoryIndexer] = None
        self.searcher: Optional[MemorySearcher] = None

        # File watcher
        self._watcher = None
        self._dirty = False
        self._last_sync: Optional[datetime] = None

    def initialize(self) -> None:
        """Initialize memory system."""
        # Initialize database
        self.storage.initialize()

        # Create embedding provider if not provided
        if self.embedding is None:
            self.embedding = self._create_default_embedding()

        # Initialize indexer
        self.indexer = MemoryIndexer(
            self.storage,
            self.embedding,
            self.config.chunking
        )

        # Initialize searcher
        self.searcher = MemorySearcher(
            self.storage,
            self.embedding,
            self.config.hybrid_search
        )

        # Create default memory files if they don't exist
        self._ensure_memory_files()

        # Perform initial sync
        asyncio.run(self.sync())

        # Start file watcher if enabled
        if self.config.sync.watch:
            self._start_watcher()

    def _create_default_embedding(self) -> EmbeddingProvider:
        """Create default embedding provider."""
        from .embeddings import OpenAIEmbeddingProvider

        # Try to load from environment or config
        import os
        api_key = os.getenv("OPENAI_API_KEY", "")

        if not api_key:
            raise ValueError(
                "No embedding provider configured. "
                "Please provide an embedding provider or set OPENAI_API_KEY."
            )

        return OpenAIEmbeddingProvider(api_key=api_key)

    def _ensure_memory_files(self) -> None:
        """Ensure default memory files exist."""
        # Create MEMORY.md if it doesn't exist
        if not self.memory_file.exists():
            self.memory_file.write_text(
                "# Long-term Memory\n\n"
                "This file contains curated persistent memory for BitwiseAI.\n\n"
                "## Contents\n\n"
            )

        # Create today's memory file if it doesn't exist
        today_path = self.get_short_term_memory_path()
        if not today_path.exists():
            today_path.write_text(self._create_short_term_header())

    def _create_short_term_header(self, date: Optional[datetime] = None) -> str:
        """Create header for short-term memory file."""
        date = date or datetime.now()
        return (
            f"# Session {date.strftime('%Y-%m-%d')}\n\n"
            f"## Metadata\n"
            f"- Created: {date.isoformat()}\n"
            f"- Source: auto-generated\n\n"
            f"## Content\n\n"
        )

    # === Dual-layer memory API ===

    def get_short_term_memory_path(self, date: Optional[datetime] = None) -> Path:
        """Get path for short-term memory file."""
        date = date or datetime.now()
        return self.memory_dir / f"{date.strftime('%Y-%m-%d')}.md"

    def get_long_term_memory_path(self) -> Path:
        """Get path for long-term memory file."""
        return self.memory_file

    def append_to_short_term(
        self,
        content: str,
        date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Append content to short-term memory.

        Args:
            content: Content to append
            date: Date for the memory file (default: today)
            metadata: Optional metadata
        """
        date = date or datetime.now()
        memory_path = self.get_short_term_memory_path(date)

        # Create file if it doesn't exist
        if not memory_path.exists():
            memory_path.write_text(self._create_short_term_header(date))

        # Append content
        timestamp = datetime.now().strftime('%H:%M:%S')
        entry = f"\n### {timestamp}\n\n{content}\n"

        with open(memory_path, 'a', encoding='utf-8') as f:
            f.write(entry)

        # Mark as dirty for reindexing
        self._dirty = True

    def promote_to_long_term(
        self,
        content: str,
        summary: Optional[str] = None
    ) -> None:
        """
        Promote content to long-term memory.

        Args:
            content: Content to add
            summary: Optional summary/title
        """
        timestamp = datetime.now().isoformat()

        entry = f"\n## Entry: {timestamp}\n\n"
        if summary:
            entry += f"**Summary:** {summary}\n\n"
        entry += f"{content}\n"

        with open(self.memory_file, 'a', encoding='utf-8') as f:
            f.write(entry)

        # Mark as dirty for reindexing
        self._dirty = True

    def compact_short_term(
        self,
        days_to_keep: int = 7,
        strategy: str = "summarize"
    ) -> CompactResult:
        """
        Compact short-term memory files.

        Args:
            days_to_keep: Number of days to keep
            strategy: Compaction strategy ("summarize", "archive", "delete")

        Returns:
            CompactResult with statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        files_compacted = 0
        files_archived = 0
        summaries_generated = 0

        for memory_file in self.memory_dir.glob("*.md"):
            try:
                # Parse date from filename
                file_date = datetime.strptime(
                    memory_file.stem,
                    "%Y-%m-%d"
                )

                if file_date < cutoff_date:
                    if strategy == "summarize":
                        # Summarize and promote to long-term
                        content = memory_file.read_text()
                        # Simple summary: first 500 chars
                        summary = content[:500].replace('\n', ' ')
                        self.promote_to_long_term(
                            f"Summary of {file_date.date()}:\n\n{summary}",
                            f"Daily summary for {file_date.date()}"
                        )
                        summaries_generated += 1

                    elif strategy == "archive":
                        # Move to archive directory
                        archive_dir = self.workspace_dir / "archive"
                        archive_dir.mkdir(exist_ok=True)
                        memory_file.rename(archive_dir / memory_file.name)
                        files_archived += 1

                    else:  # delete
                        memory_file.unlink()

                    files_compacted += 1

            except ValueError:
                # File doesn't match date pattern
                continue
            except Exception:
                continue

        return CompactResult(
            files_compacted=files_compacted,
            files_archived=files_archived,
            summaries_generated=summaries_generated
        )

    # === Search API ===

    async def search(
        self,
        query: str,
        max_results: int = 10,
        source_filter: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Search memory.

        Args:
            query: Search query
            max_results: Maximum number of results
            source_filter: Filter by source types

        Returns:
            List of search results
        """
        if self.searcher is None:
            raise RuntimeError("Memory manager not initialized")

        # Sync if dirty
        if self._dirty or self.config.sync.on_search:
            await self.sync()

        return await self.searcher.search(
            query,
            max_results=max_results,
            source_filter=source_filter
        )

    def search_sync(
        self,
        query: str,
        max_results: int = 10,
        source_filter: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Synchronous version of search."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self.search(query, max_results, source_filter)
            )
        except RuntimeError:
            return asyncio.run(
                self.search(query, max_results, source_filter)
            )

    # === Index management ===

    async def sync(self, force: bool = False) -> SyncResult:
        """
        Sync memory files to index.

        Args:
            force: Force reindex all files

        Returns:
            SyncResult with statistics
        """
        if self.indexer is None:
            raise RuntimeError("Memory manager not initialized")

        files_synced = 0
        files_removed = 0
        chunks_indexed = 0
        errors = []

        # Get list of files in database
        db_files = {f[0]: f for f in self.storage.get_all_files()}

        # Index MEMORY.md
        if self.memory_file.exists():
            result = self.indexer.index_memory_file(
                str(self.memory_file),
                str(self.workspace_dir)
            )
            if result.success:
                files_synced += 1
                chunks_indexed += result.chunks_indexed
            else:
                errors.append(f"MEMORY.md: {result.error}")

        # Index short-term memory files
        for memory_file in self.memory_dir.glob("*.md"):
            result = self.indexer.index_memory_file(
                str(memory_file),
                str(self.workspace_dir)
            )
            if result.success:
                files_synced += 1
                chunks_indexed += result.chunks_indexed
            else:
                errors.append(f"{memory_file.name}: {result.error}")

        # Remove index for deleted files
        current_files = {str(self.memory_file)} | {
            str(f) for f in self.memory_dir.glob("*.md")
        }

        for db_path in list(db_files.keys()):
            if db_files[db_path][1] == "memory":  # source == memory
                if db_path not in current_files:
                    self.storage.delete_chunks_by_path(db_path, "memory")
                    self.storage.delete_file(db_path, "memory")
                    files_removed += 1

        self._dirty = False
        self._last_sync = datetime.now()

        return SyncResult(
            files_synced=files_synced,
            files_removed=files_removed,
            chunks_indexed=chunks_indexed,
            errors=errors
        )

    def index_skill(self, skill_path: str, skill_metadata: Dict[str, Any], content: str) -> None:
        """Index a skill."""
        if self.indexer is None:
            raise RuntimeError("Memory manager not initialized")

        self.indexer.index_skill(skill_path, skill_metadata, content)

    def index_document(self, doc_path: str, content: str) -> IndexResult:
        """Index a document."""
        if self.indexer is None:
            raise RuntimeError("Memory manager not initialized")

        return self.indexer.index_document(doc_path, content)

    def remove_index(self, path: str) -> None:
        """Remove index for a path."""
        # Try all sources
        for source in ["memory", "docs", "skills", "sessions"]:
            self.storage.delete_chunks_by_path(path, source)
            self.storage.delete_file(path, source)

    # === Status queries ===

    def status(self) -> MemoryStatus:
        """Get memory system status."""
        files, chunks, _ = self.storage.get_stats()

        return MemoryStatus(
            initialized=self.indexer is not None,
            files=files,
            chunks=chunks,
            vector_enabled=self.config.vector_enabled,
            fts_enabled=True,
            watching=self._watcher is not None and self._watcher.is_running(),
            last_sync=self._last_sync
        )

    def stats(self) -> MemoryStats:
        """Get memory system statistics."""
        files, chunks, cache_entries = self.storage.get_stats()
        db_size = self.storage.get_db_size()

        # Calculate average chunk size
        avg_chunk_size = 0.0
        if chunks > 0:
            # Rough estimate
            avg_chunk_size = db_size / chunks if chunks > 0 else 0

        return MemoryStats(
            total_files=files,
            total_chunks=chunks,
            total_vectors=chunks if self.config.vector_enabled else 0,
            cache_entries=cache_entries,
            db_size_bytes=db_size,
            avg_chunk_size=avg_chunk_size
        )

    # === File watching ===

    def _start_watcher(self) -> None:
        """Start file watcher."""
        watch_paths = [
            str(self.memory_file),
            str(self.memory_dir),
        ]

        self._watcher = create_file_watcher(
            watch_paths,
            self._on_file_changed,
            debounce_ms=self.config.sync.watch_debounce_ms
        )
        self._watcher.start()

    def _stop_watcher(self) -> None:
        """Stop file watcher."""
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def _on_file_changed(self, file_path: str, event_type: str) -> None:
        """Handle file change event."""
        self._dirty = True

    # === Cleanup ===

    def close(self) -> None:
        """Close memory manager and release resources."""
        self._stop_watcher()
        self.storage.close()

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
