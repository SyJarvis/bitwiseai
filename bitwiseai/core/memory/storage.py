"""
SQLite storage backend for the memory system.
"""

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schema import Queries, Schema, check_schema_version, get_schema_version_sql
from .types import ChunkRecord, FTSSearchResult, VectorSearchResult


class SQLiteStorage:
    """SQLite storage backend for memory data."""

    def __init__(
        self,
        db_path: str = "~/.bitwiseai/memory.db",
        vector_enabled: bool = True,
        vector_extension_path: Optional[str] = None
    ):
        """
        Initialize SQLite storage.

        Args:
            db_path: Database file path
            vector_enabled: Whether to enable vector search (requires sqlite-vec extension)
            vector_extension_path: Path to sqlite-vec extension (optional)
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.vector_enabled = vector_enabled
        self.vector_extension_path = vector_extension_path
        self._vector_ready = False
        self._vector_dims: Optional[int] = None

        self._local = threading.local()
        self._lock = threading.RLock()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            self._local.connection.row_factory = sqlite3.Row
            self._enable_wal_mode()

        return self._local.connection

    def _enable_wal_mode(self):
        """Enable WAL mode for better concurrency."""
        conn = self._local.connection
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

    def initialize(self) -> None:
        """Initialize database schema."""
        with self._lock:
            conn = self._get_connection()

            # Create tables
            for sql in Schema.get_create_tables_sql():
                conn.execute(sql)

            # Create FTS table
            conn.execute(Schema.get_create_fts_table_sql())

            # Create FTS triggers
            for trigger_sql in Schema.get_create_fts_triggers_sql():
                try:
                    conn.execute(trigger_sql)
                except sqlite3.OperationalError:
                    # Trigger might already exist
                    pass

            # Store schema version
            conn.execute(get_schema_version_sql(), ("1.0.0",))

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    def _ensure_vector_table(self, dimensions: int) -> bool:
        """Ensure vector table exists and is ready."""
        if not self.vector_enabled:
            return False

        if self._vector_ready and self._vector_dims == dimensions:
            return True

        with self._lock:
            conn = self._get_connection()

            # Try to load sqlite-vec extension
            if self.vector_extension_path:
                try:
                    conn.enable_load_extension(True)
                    conn.load_extension(self.vector_extension_path)
                except Exception:
                    pass

            # Create vector table
            try:
                sql = Schema.get_create_vector_table_sql(dimensions)
                conn.execute(sql)
                self._vector_ready = True
                self._vector_dims = dimensions
                return True
            except Exception:
                self._vector_ready = False
                return False

    # === File operations ===

    def upsert_file(
        self,
        path: str,
        source: str,
        file_hash: str,
        mtime: int,
        size: int
    ) -> None:
        """Insert or update file record."""
        with self._lock:
            conn = self._get_connection()
            conn.execute(Queries.UPSERT_FILE, (path, source, file_hash, mtime, size))

    def delete_file(self, path: str, source: Optional[str] = None) -> None:
        """Delete file record."""
        with self._lock:
            conn = self._get_connection()
            if source:
                conn.execute(Queries.DELETE_FILE_BY_SOURCE, (path, source))
            else:
                conn.execute(Queries.DELETE_FILE, (path,))

    def get_file_hash(self, path: str, source: str) -> Optional[str]:
        """Get file hash."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(Queries.GET_FILE_HASH, (path, source))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_all_files(self, source: Optional[str] = None) -> List[Tuple[str, str, str, int, int]]:
        """Get all files, optionally filtered by source."""
        with self._lock:
            conn = self._get_connection()
            if source:
                cursor = conn.execute(Queries.GET_FILES_BY_SOURCE, (source,))
            else:
                cursor = conn.execute(Queries.GET_ALL_FILES)
            return [(row[0], row[1], row[2], row[3], row[4]) for row in cursor.fetchall()]

    # === Chunk operations ===

    def upsert_chunk(self, chunk: ChunkRecord) -> None:
        """Insert or update chunk."""
        with self._lock:
            conn = self._get_connection()

            # Serialize embedding to JSON
            embedding_json = json.dumps(chunk.embedding) if chunk.embedding else "[]"

            conn.execute(Queries.UPSERT_CHUNK, (
                chunk.id,
                chunk.path,
                chunk.source,
                chunk.start_line,
                chunk.end_line,
                chunk.hash,
                chunk.model,
                chunk.text,
                embedding_json,
                chunk.updated_at or int(time.time())
            ))

            # Also insert into vector table if available
            if self._vector_ready and chunk.embedding:
                self._upsert_vector(chunk.id, chunk.embedding)

    def _upsert_vector(self, chunk_id: str, embedding: List[float]) -> None:
        """Insert or update vector in sqlite-vec table."""
        if not self._vector_ready:
            return

        conn = self._get_connection()

        # Check if chunk exists
        cursor = conn.execute("SELECT chunk_id FROM chunks_vec WHERE chunk_id = ?", (chunk_id,))
        if cursor.fetchone():
            # Update
            conn.execute(
                "UPDATE chunks_vec SET embedding = ? WHERE chunk_id = ?",
                (json.dumps(embedding), chunk_id)
            )
        else:
            # Insert
            conn.execute(
                "INSERT INTO chunks_vec (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, json.dumps(embedding))
            )

    def delete_chunks_by_path(self, path: str, source: str) -> int:
        """Delete all chunks for a path. Returns number of deleted chunks."""
        with self._lock:
            conn = self._get_connection()

            # Get chunk IDs for vector table deletion
            cursor = conn.execute(
                "SELECT id FROM chunks WHERE path = ? AND source = ?",
                (path, source)
            )
            chunk_ids = [row[0] for row in cursor.fetchall()]

            # Delete from chunks table (triggers will handle FTS)
            cursor = conn.execute(Queries.DELETE_CHUNKS_BY_PATH, (path, source))
            deleted = cursor.rowcount

            # Delete from vector table
            if self._vector_ready and chunk_ids:
                placeholders = ','.join('?' * len(chunk_ids))
                conn.execute(f"DELETE FROM chunks_vec WHERE chunk_id IN ({placeholders})", chunk_ids)

            return deleted

    def get_chunks_by_path(self, path: str, source: str) -> List[ChunkRecord]:
        """Get all chunks for a path."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(Queries.GET_CHUNKS_BY_PATH, (path, source))

            chunks = []
            for row in cursor.fetchall():
                embedding = json.loads(row[8]) if row[8] else None
                chunks.append(ChunkRecord(
                    id=row[0],
                    path=row[1],
                    source=row[2],
                    start_line=row[3],
                    end_line=row[4],
                    hash=row[5],
                    model=row[6],
                    text=row[7],
                    embedding=embedding,
                    updated_at=row[9]
                ))

            return chunks

    def get_chunk_by_id(self, chunk_id: str) -> Optional[ChunkRecord]:
        """Get chunk by ID."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT id, path, source, start_line, end_line, hash, model, text, embedding, updated_at "
                "FROM chunks WHERE id = ?",
                (chunk_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            embedding = json.loads(row[8]) if row[8] else None
            return ChunkRecord(
                id=row[0],
                path=row[1],
                source=row[2],
                start_line=row[3],
                end_line=row[4],
                hash=row[5],
                model=row[6],
                text=row[7],
                embedding=embedding,
                updated_at=row[9]
            )

    def get_chunk_count(self, source: Optional[str] = None) -> int:
        """Get total number of chunks."""
        with self._lock:
            conn = self._get_connection()
            if source:
                cursor = conn.execute(Queries.GET_CHUNK_COUNT_BY_SOURCE, (source,))
            else:
                cursor = conn.execute(Queries.GET_CHUNK_COUNT)
            return cursor.fetchone()[0]

    # === Vector search ===

    def search_vectors(
        self,
        query_vec: List[float],
        limit: int = 10,
        source_filter: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        if not self._vector_ready:
            # Fall back to manual cosine similarity
            return self._search_vectors_manual(query_vec, limit, source_filter)

        with self._lock:
            conn = self._get_connection()

            try:
                # Use sqlite-vec for vector search
                query_vec_json = json.dumps(query_vec)

                if source_filter:
                    # Get chunk IDs first, then filter
                    placeholders = ','.join('?' * len(source_filter))
                    sql = f"""
                    SELECT chunk_id, distance
                    FROM chunks_vec
                    WHERE embedding MATCH ? AND k = ?
                    """
                    cursor = conn.execute(sql, (query_vec_json, limit * 2))

                    results = []
                    for row in cursor.fetchall():
                        # Check if chunk is in source filter
                        chunk = self.get_chunk_by_id(row[0])
                        if chunk and chunk.source in source_filter:
                            # Convert distance to similarity (1 - distance)
                            similarity = 1.0 - row[1]
                            results.append(VectorSearchResult(
                                chunk_id=row[0],
                                score=similarity
                            ))
                            if len(results) >= limit:
                                break

                    return results
                else:
                    sql = """
                    SELECT chunk_id, distance
                    FROM chunks_vec
                    WHERE embedding MATCH ? AND k = ?
                    """
                    cursor = conn.execute(sql, (query_vec_json, limit))

                    return [
                        VectorSearchResult(
                            chunk_id=row[0],
                            score=1.0 - row[1]  # Convert distance to similarity
                        )
                        for row in cursor.fetchall()
                    ]
            except Exception:
                # Fall back to manual search
                return self._search_vectors_manual(query_vec, limit, source_filter)

    def _search_vectors_manual(
        self,
        query_vec: List[float],
        limit: int = 10,
        source_filter: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        """Manual cosine similarity search (fallback)."""
        with self._lock:
            conn = self._get_connection()

            # Get all chunks with embeddings
            if source_filter:
                placeholders = ','.join('?' * len(source_filter))
                sql = f"""
                SELECT id, embedding FROM chunks
                WHERE source IN ({placeholders}) AND embedding != '[]'
                """
                cursor = conn.execute(sql, source_filter)
            else:
                cursor = conn.execute("SELECT id, embedding FROM chunks WHERE embedding != '[]'")

            # Calculate cosine similarity
            results = []
            query_norm = sum(x * x for x in query_vec) ** 0.5

            for row in cursor.fetchall():
                embedding = json.loads(row[1])
                if not embedding:
                    continue

                # Cosine similarity
                dot_product = sum(a * b for a, b in zip(query_vec, embedding))
                embedding_norm = sum(x * x for x in embedding) ** 0.5

                if embedding_norm > 0 and query_norm > 0:
                    similarity = dot_product / (query_norm * embedding_norm)
                    results.append(VectorSearchResult(
                        chunk_id=row[0],
                        score=similarity
                    ))

            # Sort by score and return top results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]

    # === FTS operations ===

    def search_fts(
        self,
        query: str,
        limit: int = 10,
        source_filter: Optional[List[str]] = None
    ) -> List[FTSSearchResult]:
        """Full-text search using BM25."""
        with self._lock:
            conn = self._get_connection()

            # Build FTS query (simple AND of all terms)
            terms = query.split()
            fts_query = ' AND '.join(f'"{term}"' for term in terms)

            try:
                if source_filter and len(source_filter) == 1:
                    # Single source filter
                    cursor = conn.execute(
                        Queries.SEARCH_FTS_WITH_SOURCE,
                        (fts_query, source_filter[0], limit)
                    )
                else:
                    # No filter or multiple sources (post-filter)
                    cursor = conn.execute(Queries.SEARCH_FTS, (fts_query, limit))

                results = []
                for row in cursor.fetchall():
                    # BM25 rank is negative (more negative = less relevant)
                    # Convert to 0-1 score where 1 is most relevant
                    rank = row[1]
                    # Simple conversion: higher rank (less negative) = higher score
                    score = 1.0 / (1.0 + abs(rank))

                    results.append(FTSSearchResult(
                        chunk_id=row[0],
                        score=score
                    ))

                # Post-filter by source if needed
                if source_filter and len(source_filter) > 1:
                    filtered_results = []
                    for r in results:
                        chunk = self.get_chunk_by_id(r.chunk_id)
                        if chunk and chunk.source in source_filter:
                            filtered_results.append(r)
                    results = filtered_results[:limit]

                return results
            except sqlite3.OperationalError:
                # FTS table might not exist or query error
                return []

    # === Embedding cache ===

    def get_cached_embedding(self, text_hash: str, provider_key: str) -> Optional[List[float]]:
        """Get cached embedding."""
        with self._lock:
            conn = self._get_connection()

            # Parse provider key (format: "provider:model")
            parts = provider_key.split(':', 1)
            provider = parts[0]
            model = parts[1] if len(parts) > 1 else ""

            cursor = conn.execute(
                Queries.GET_CACHED_EMBEDDING,
                (provider, model, provider_key, text_hash)
            )
            row = cursor.fetchone()

            if row:
                return json.loads(row[0])
            return None

    def cache_embedding(
        self,
        text_hash: str,
        provider_key: str,
        embedding: List[float],
        dims: int
    ) -> None:
        """Cache embedding."""
        with self._lock:
            conn = self._get_connection()

            # Parse provider key
            parts = provider_key.split(':', 1)
            provider = parts[0]
            model = parts[1] if len(parts) > 1 else ""

            conn.execute(
                Queries.CACHE_EMBEDDING,
                (
                    provider,
                    model,
                    provider_key,
                    text_hash,
                    json.dumps(embedding),
                    dims,
                    int(time.time())
                )
            )

    def prune_embedding_cache(self, max_entries: int) -> int:
        """Prune old cache entries. Returns number of entries removed."""
        with self._lock:
            conn = self._get_connection()

            # Get current count
            cursor = conn.execute(Queries.GET_CACHE_COUNT)
            current_count = cursor.fetchone()[0]

            if current_count <= max_entries:
                return 0

            # Remove oldest entries
            cursor = conn.execute(Queries.PRUNE_CACHE, (max_entries,))
            return cursor.rowcount

    def get_cache_count(self) -> int:
        """Get number of cached embeddings."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(Queries.GET_CACHE_COUNT)
            return cursor.fetchone()[0]

    # === Stats ===

    def get_stats(self) -> Tuple[int, int, int]:
        """Get statistics (files, chunks, cache_entries)."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(Queries.GET_STATS)
            row = cursor.fetchone()
            return (row[0], row[1], row[2])

    def get_db_size(self) -> int:
        """Get database file size in bytes."""
        try:
            return self.db_path.stat().st_size
        except Exception:
            return 0
