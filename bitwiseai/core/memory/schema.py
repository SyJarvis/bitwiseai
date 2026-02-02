"""
Database schema for the memory system.
"""

from typing import List, Optional


class Schema:
    """Database schema definitions."""

    @staticmethod
    def get_create_tables_sql() -> List[str]:
        """Get all CREATE TABLE statements."""
        statements = [
            Schema.CREATE_META_TABLE,
            Schema.CREATE_FILES_TABLE,
            Schema.CREATE_CHUNKS_TABLE,
            Schema.CREATE_EMBEDDING_CACHE_TABLE,
        ]
        # Add index statements (CREATE_INDEXES is a list)
        statements.extend(Schema.CREATE_INDEXES)
        return statements

    # Meta table for storing metadata
    CREATE_META_TABLE = """
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """

    # Files table tracks memory files
    CREATE_FILES_TABLE = """
    CREATE TABLE IF NOT EXISTS files (
        path TEXT PRIMARY KEY,
        source TEXT NOT NULL DEFAULT 'memory',
        hash TEXT NOT NULL,
        mtime INTEGER NOT NULL,
        size INTEGER NOT NULL
    );
    """

    # Chunks table stores indexed content
    CREATE_CHUNKS_TABLE = """
    CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,
        path TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'memory',
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        hash TEXT NOT NULL,
        model TEXT NOT NULL,
        text TEXT NOT NULL,
        embedding TEXT NOT NULL,
        updated_at INTEGER NOT NULL
    );
    """

    # Embedding cache for efficiency
    CREATE_EMBEDDING_CACHE_TABLE = """
    CREATE TABLE IF NOT EXISTS embedding_cache (
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        provider_key TEXT NOT NULL,
        hash TEXT NOT NULL,
        embedding TEXT NOT NULL,
        dims INTEGER,
        updated_at INTEGER NOT NULL,
        PRIMARY KEY (provider, model, provider_key, hash)
    );
    """

    # Indexes for performance (each must be a separate statement)
    CREATE_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);",
        "CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source);",
        "CREATE INDEX IF NOT EXISTS idx_chunks_updated ON chunks(updated_at);",
        "CREATE INDEX IF NOT EXISTS idx_files_source ON files(source);",
    ]

    @staticmethod
    def get_create_fts_table_sql() -> str:
        """Get CREATE VIRTUAL TABLE statement for FTS5."""
        return """
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            chunk_id,
            text,
            path,
            source,
            start_line,
            end_line,
            content='chunks',
            content_rowid='rowid'
        );
        """

    @staticmethod
    def get_create_fts_triggers_sql() -> List[str]:
        """Get triggers to keep FTS index in sync."""
        return [
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_insert AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(chunk_id, text, path, source, start_line, end_line)
                VALUES (new.id, new.text, new.path, new.source, new.start_line, new.end_line);
            END;
            """,
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_delete AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, text, path, source, start_line, end_line)
                VALUES ('delete', old.rowid, old.id, old.text, old.path, old.source, old.start_line, old.end_line);
            END;
            """,
            """
            CREATE TRIGGER IF NOT EXISTS chunks_fts_update AFTER UPDATE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, chunk_id, text, path, source, start_line, end_line)
                VALUES ('delete', old.rowid, old.id, old.text, old.path, old.source, old.start_line, old.end_line);
                INSERT INTO chunks_fts(chunk_id, text, path, source, start_line, end_line)
                VALUES (new.id, new.text, new.path, new.source, new.start_line, new.end_line);
            END;
            """,
        ]

    @staticmethod
    def get_create_vector_table_sql(dimensions: int) -> str:
        """
        Get CREATE VIRTUAL TABLE statement for sqlite-vec.

        Args:
            dimensions: Number of dimensions in the embedding vectors
        """
        return f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
            chunk_id TEXT PRIMARY KEY,
            embedding FLOAT[{dimensions}]
        );
        """

    @staticmethod
    def get_drop_tables_sql() -> List[str]:
        """Get DROP TABLE statements for cleanup."""
        return [
            "DROP TABLE IF EXISTS chunks_fts;",
            "DROP TABLE IF EXISTS chunks_vec;",
            "DROP TABLE IF EXISTS chunks;",
            "DROP TABLE IF EXISTS files;",
            "DROP TABLE IF EXISTS embedding_cache;",
            "DROP TABLE IF EXISTS meta;",
        ]


# SQL queries for common operations

class Queries:
    """SQL queries for common operations."""

    # File operations
    UPSERT_FILE = """
    INSERT INTO files (path, source, hash, mtime, size)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(path) DO UPDATE SET
        source = excluded.source,
        hash = excluded.hash,
        mtime = excluded.mtime,
        size = excluded.size;
    """

    DELETE_FILE = "DELETE FROM files WHERE path = ?;"
    DELETE_FILE_BY_SOURCE = "DELETE FROM files WHERE path = ? AND source = ?;"
    GET_FILE_HASH = "SELECT hash FROM files WHERE path = ? AND source = ?;"
    GET_ALL_FILES = "SELECT path, source, hash, mtime, size FROM files;"
    GET_FILES_BY_SOURCE = "SELECT path, source, hash, mtime, size FROM files WHERE source = ?;"

    # Chunk operations
    UPSERT_CHUNK = """
    INSERT INTO chunks (id, path, source, start_line, end_line, hash, model, text, embedding, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        path = excluded.path,
        source = excluded.source,
        start_line = excluded.start_line,
        end_line = excluded.end_line,
        hash = excluded.hash,
        model = excluded.model,
        text = excluded.text,
        embedding = excluded.embedding,
        updated_at = excluded.updated_at;
    """

    DELETE_CHUNKS_BY_PATH = "DELETE FROM chunks WHERE path = ? AND source = ?;"
    GET_CHUNKS_BY_PATH = "SELECT id, path, source, start_line, end_line, hash, model, text, embedding, updated_at FROM chunks WHERE path = ? AND source = ?;"
    GET_CHUNK_COUNT = "SELECT COUNT(*) FROM chunks;"
    GET_CHUNK_COUNT_BY_SOURCE = "SELECT COUNT(*) FROM chunks WHERE source = ?;"

    # FTS operations
    SEARCH_FTS = """
    SELECT chunk_id, rank
    FROM chunks_fts
    WHERE chunks_fts MATCH ?
    ORDER BY rank
    LIMIT ?;
    """

    SEARCH_FTS_WITH_SOURCE = """
    SELECT chunk_id, rank
    FROM chunks_fts
    WHERE chunks_fts MATCH ? AND source = ?
    ORDER BY rank
    LIMIT ?;
    """

    # Embedding cache operations
    GET_CACHED_EMBEDDING = """
    SELECT embedding FROM embedding_cache
    WHERE provider = ? AND model = ? AND provider_key = ? AND hash = ?;
    """

    CACHE_EMBEDDING = """
    INSERT INTO embedding_cache (provider, model, provider_key, hash, embedding, dims, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(provider, model, provider_key, hash) DO UPDATE SET
        embedding = excluded.embedding,
        dims = excluded.dims,
        updated_at = excluded.updated_at;
    """

    PRUNE_CACHE = """
    DELETE FROM embedding_cache
    WHERE rowid NOT IN (
        SELECT rowid FROM embedding_cache
        ORDER BY updated_at DESC
        LIMIT ?
    );
    """

    GET_CACHE_COUNT = "SELECT COUNT(*) FROM embedding_cache;"

    # Stats
    GET_STATS = """
    SELECT
        (SELECT COUNT(*) FROM files) as total_files,
        (SELECT COUNT(*) FROM chunks) as total_chunks,
        (SELECT COUNT(*) FROM embedding_cache) as cache_entries;
    """


# Version tracking
SCHEMA_VERSION = "1.0.0"


def get_schema_version_sql() -> str:
    """Get SQL to store schema version."""
    return """
    INSERT OR REPLACE INTO meta (key, value)
    VALUES ('schema_version', ?);
    """


def check_schema_version(conn) -> bool:
    """Check if the database schema version matches."""
    try:
        cursor = conn.execute("SELECT value FROM meta WHERE key = 'schema_version';")
        row = cursor.fetchone()
        if row is None:
            return False
        return row[0] == SCHEMA_VERSION
    except Exception:
        return False
