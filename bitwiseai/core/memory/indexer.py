"""
Memory indexer for chunking and indexing content.
"""

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .chunker import MarkdownChunker
from .storage import SQLiteStorage
from .types import (
    ChunkConfig,
    ChunkRecord,
    EmbeddingProvider,
    IndexResult,
    MemoryChunk,
)


class MemoryIndexer:
    """Content indexer - responsible for chunking, embedding generation and storage."""

    def __init__(
        self,
        storage: SQLiteStorage,
        embedding_provider: EmbeddingProvider,
        chunk_config: Optional[ChunkConfig] = None
    ):
        """
        Initialize indexer.

        Args:
            storage: SQLite storage instance
            embedding_provider: Embedding provider
            chunk_config: Chunking configuration
        """
        self.storage = storage
        self.embedding = embedding_provider
        self.chunk_config = chunk_config or ChunkConfig()
        self.chunker = MarkdownChunker(self.chunk_config)

    def index_file(
        self,
        file_path: str,
        content: str,
        source: str,
        mtime: Optional[int] = None
    ) -> IndexResult:
        """
        Index a single file.

        Args:
            file_path: Path to the file
            content: File content
            source: Source type (memory, docs, skills, etc.)
            mtime: Modification time (optional)

        Returns:
            IndexResult with statistics
        """
        try:
            # Calculate file hash
            content_hash = self._calculate_hash(content)

            # Check if file needs reindexing
            stored_hash = self.storage.get_file_hash(file_path, source)
            if stored_hash == content_hash:
                # File unchanged, skip
                return IndexResult(
                    file_path=file_path,
                    chunks_indexed=0,
                    chunks_skipped=self.storage.get_chunk_count(source),
                    success=True
                )

            # Get mtime
            if mtime is None:
                try:
                    mtime = int(Path(file_path).stat().st_mtime)
                except Exception:
                    mtime = int(time.time())

            # Delete old chunks
            self.storage.delete_chunks_by_path(file_path, source)

            # Chunk content
            chunks = self.chunker.chunk(content, file_path, source)

            if not chunks:
                # Update file record even if no chunks
                self.storage.upsert_file(
                    file_path,
                    source,
                    content_hash,
                    mtime,
                    len(content)
                )
                return IndexResult(
                    file_path=file_path,
                    chunks_indexed=0,
                    chunks_skipped=0,
                    success=True
                )

            # Generate embeddings
            embeddings = self._embed_chunks_sync(chunks)

            # Store chunks
            for i, chunk in enumerate(chunks):
                record = ChunkRecord(
                    id=chunk.id,
                    path=chunk.path,
                    source=chunk.source,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    hash=chunk.hash,
                    model=self.embedding.model,
                    text=chunk.text,
                    embedding=embeddings[i] if i < len(embeddings) else None,
                    updated_at=int(time.time())
                )
                self.storage.upsert_chunk(record)

            # Update file record
            self.storage.upsert_file(
                file_path,
                source,
                content_hash,
                mtime,
                len(content)
            )

            return IndexResult(
                file_path=file_path,
                chunks_indexed=len(chunks),
                chunks_skipped=0,
                success=True
            )

        except Exception as e:
            return IndexResult(
                file_path=file_path,
                chunks_indexed=0,
                chunks_skipped=0,
                success=False,
                error=str(e)
            )

    def index_memory_file(self, abs_path: str, workspace_dir: str) -> IndexResult:
        """Index a memory file (MEMORY.md or memory/*.md)."""
        try:
            content = Path(abs_path).read_text(encoding='utf-8')
            return self.index_file(abs_path, content, "memory")
        except Exception as e:
            return IndexResult(
                file_path=abs_path,
                chunks_indexed=0,
                chunks_skipped=0,
                success=False,
                error=str(e)
            )

    def index_skill(
        self,
        skill_path: str,
        skill_metadata: Dict[str, Any],
        content: str
    ) -> IndexResult:
        """Index a skill file."""
        # Create enriched content with metadata
        enriched_content = self._create_skill_index_text(skill_metadata, content)
        return self.index_file(skill_path, enriched_content, "skills")

    def index_document(self, doc_path: str, content: str) -> IndexResult:
        """Index a document."""
        return self.index_file(doc_path, content, "docs")

    def delete_index(self, path: str, source: str) -> None:
        """Delete index for a path."""
        self.storage.delete_chunks_by_path(path, source)
        self.storage.delete_file(path, source)

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _embed_chunks_sync(self, chunks: List[MemoryChunk]) -> List[List[float]]:
        """
        Generate embeddings for chunks (synchronous version).

        This is a synchronous wrapper around the async embedding method.
        """
        import asyncio

        if not chunks:
            return []

        # Get texts
        texts = [chunk.text for chunk in chunks]

        # Check cache first
        provider_key = self.embedding.get_provider_key()
        cached_embeddings = []
        texts_to_embed = []
        text_indices = []

        for i, text in enumerate(texts):
            text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
            cached = self.storage.get_cached_embedding(text_hash, provider_key)

            if cached:
                cached_embeddings.append((i, cached))
            else:
                texts_to_embed.append(text)
                text_indices.append(i)

        if texts_to_embed:
            # Embed texts (synchronous)
            try:
                # First try: use asyncio.run() which creates a new event loop
                new_embeddings = asyncio.run(
                    self.embedding.embed_batch(texts_to_embed)
                )
            except RuntimeError as e:
                # Last resort: create a new thread with its own event loop
                import threading
                result = [None]
                exception = [None]
                
                def run_embed():
                    try:
                        result[0] = asyncio.run(
                            self.embedding.embed_batch(texts_to_embed)
                        )
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=run_embed)
                thread.start()
                thread.join()
                
                if exception[0]:
                    raise exception[0]
                new_embeddings = result[0]

            # Cache new embeddings
            for idx, text_idx in enumerate(text_indices):
                text = texts_to_embed[idx]
                text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
                self.storage.cache_embedding(
                    text_hash,
                    provider_key,
                    new_embeddings[idx],
                    len(new_embeddings[idx])
                )
                cached_embeddings.append((text_idx, new_embeddings[idx]))

        # Reconstruct in original order
        embeddings = [None] * len(chunks)
        for idx, embedding in cached_embeddings:
            embeddings[idx] = embedding

        return embeddings

    async def _embed_chunks(self, chunks: List[MemoryChunk]) -> List[List[float]]:
        """
        Generate embeddings for chunks (async version).

        Args:
            chunks: Chunks to embed

        Returns:
            List of embeddings
        """
        if not chunks:
            return []

        # Get texts
        texts = [chunk.text for chunk in chunks]

        # Check cache first
        provider_key = self.embedding.get_provider_key()
        cached_embeddings = []
        texts_to_embed = []
        text_indices = []

        for i, text in enumerate(texts):
            text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
            cached = self.storage.get_cached_embedding(text_hash, provider_key)

            if cached:
                cached_embeddings.append((i, cached))
            else:
                texts_to_embed.append(text)
                text_indices.append(i)

        if texts_to_embed:
            # Embed texts
            new_embeddings = await self.embedding.embed_batch(texts_to_embed)

            # Cache new embeddings
            for idx, text_idx in enumerate(text_indices):
                text = texts_to_embed[idx]
                text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
                self.storage.cache_embedding(
                    text_hash,
                    provider_key,
                    new_embeddings[idx],
                    len(new_embeddings[idx])
                )
                cached_embeddings.append((text_idx, new_embeddings[idx]))

        # Reconstruct in original order
        embeddings = [None] * len(chunks)
        for idx, embedding in cached_embeddings:
            embeddings[idx] = embedding

        return embeddings

    def _create_skill_index_text(
        self,
        skill_metadata: Dict[str, Any],
        content: str
    ) -> str:
        """Create enriched index text for a skill."""
        parts = []

        # Add metadata fields
        if 'name' in skill_metadata:
            parts.append(f"Skill: {skill_metadata['name']}")
        if 'description' in skill_metadata:
            parts.append(f"Description: {skill_metadata['description']}")
        if 'tags' in skill_metadata:
            parts.append(f"Tags: {', '.join(skill_metadata['tags'])}")

        parts.append("---")
        parts.append(content)

        return "\n".join(parts)
