"""
Markdown chunking logic for the memory system.
"""

import hashlib
import re
import uuid
from typing import List, Optional

from .types import ChunkConfig, MemoryChunk


class MarkdownChunker:
    """Chunks markdown content into smaller pieces."""

    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        Initialize the chunker.

        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkConfig()

    def chunk(
        self,
        content: str,
        path: str,
        source: str = "memory",
        metadata: Optional[dict] = None
    ) -> List[MemoryChunk]:
        """
        Chunk markdown content into smaller pieces.

        Args:
            content: Markdown content to chunk
            path: File path for the content
            source: Source type (memory, docs, skills, etc.)
            metadata: Optional metadata to include in chunks

        Returns:
            List of memory chunks
        """
        if not content or not content.strip():
            return []

        lines = content.split('\n')
        chunks = []
        chunk_idx = 0

        current_chunk_lines = []
        current_chunk_start = 0
        current_size = 0

        for i, line in enumerate(lines):
            line_with_newline = line + '\n'
            line_size = len(line_with_newline)

            # Check if adding this line would exceed the chunk size
            if current_size + line_size > self.config.max_chars and current_chunk_lines:
                # Save current chunk
                chunk_text = ''.join(current_chunk_lines).rstrip('\n')
                chunk = self._create_chunk(
                    chunk_text,
                    path,
                    source,
                    current_chunk_start,
                    i - 1,
                    chunk_idx,
                    metadata
                )
                chunks.append(chunk)
                chunk_idx += 1

                # Start new chunk with overlap
                overlap_size = 0
                overlap_lines = []

                # Take lines from the end for overlap
                for overlap_line in reversed(current_chunk_lines):
                    if overlap_size + len(overlap_line) > self.config.overlap_chars:
                        break
                    overlap_lines.insert(0, overlap_line)
                    overlap_size += len(overlap_line)

                current_chunk_lines = overlap_lines
                current_chunk_start = i - len(overlap_lines) + 1
                current_size = overlap_size

            # Add current line
            current_chunk_lines.append(line_with_newline)
            current_size += line_size

        # Don't forget the last chunk
        if current_chunk_lines:
            chunk_text = ''.join(current_chunk_lines).rstrip('\n')
            chunk = self._create_chunk(
                chunk_text,
                path,
                source,
                current_chunk_start,
                len(lines) - 1,
                chunk_idx,
                metadata
            )
            chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        text: str,
        path: str,
        source: str,
        start_line: int,
        end_line: int,
        chunk_idx: int,
        metadata: Optional[dict] = None
    ) -> MemoryChunk:
        """Create a memory chunk."""
        # Generate a unique ID based on content hash and position
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        chunk_id = f"{source}:{path}:{chunk_idx}:{content_hash}"

        return MemoryChunk(
            id=chunk_id,
            text=text,
            start_line=start_line + 1,  # 1-indexed line numbers
            end_line=end_line + 1,
            hash=content_hash,
            path=path,
            source=source,
            metadata=metadata or {}
        )

    def chunk_with_headers(
        self,
        content: str,
        path: str,
        source: str = "memory",
        metadata: Optional[dict] = None
    ) -> List[MemoryChunk]:
        """
        Chunk markdown content, respecting header boundaries.

        This method tries to keep headers with their content and
        creates chunks at header boundaries when possible.

        Args:
            content: Markdown content to chunk
            path: File path for the content
            source: Source type
            metadata: Optional metadata

        Returns:
            List of memory chunks
        """
        if not content or not content.strip():
            return []

        lines = content.split('\n')
        chunks = []
        chunk_idx = 0

        # Find header positions (lines starting with #)
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        headers = []

        for i, line in enumerate(lines):
            match = header_pattern.match(line)
            if match:
                level = len(match.group(1))
                title = match.group(2)
                headers.append((i, level, title))

        if not headers:
            # No headers, use regular chunking
            return self.chunk(content, path, source, metadata)

        # Chunk by headers
        current_section_lines = []
        current_section_start = 0
        current_size = 0

        def save_section(end_idx: int):
            nonlocal chunk_idx
            if not current_section_lines:
                return

            chunk_text = ''.join(current_section_lines).rstrip('\n')
            chunk = self._create_chunk(
                chunk_text,
                path,
                source,
                current_section_start,
                end_idx,
                chunk_idx,
                metadata
            )
            chunks.append(chunk)
            chunk_idx += 1

        for i, line in enumerate(lines):
            line_with_newline = line + '\n'
            line_size = len(line_with_newline)

            # Check if this is a header
            is_header = any(h[0] == i for h in headers)

            # If this is a header and we have content, check if we should start a new section
            if is_header and current_section_lines:
                # Check if adding this line would exceed the chunk size
                if current_size + line_size > self.config.max_chars:
                    # Save current section
                    save_section(i - 1)
                    # Start new section
                    current_section_lines = []
                    current_section_start = i
                    current_size = 0

            current_section_lines.append(line_with_newline)
            current_size += line_size

            # If we've reached the max size, save the section
            if current_size >= self.config.max_chars:
                save_section(i)
                current_section_lines = []
                current_section_start = i + 1
                current_size = 0

        # Save the last section
        if current_section_lines:
            save_section(len(lines) - 1)

        return chunks


def create_chunker(config: Optional[ChunkConfig] = None) -> MarkdownChunker:
    """Create a markdown chunker."""
    return MarkdownChunker(config)
