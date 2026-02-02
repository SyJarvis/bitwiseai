"""
Hybrid search for the memory system.
"""

import asyncio
from typing import Dict, List, Optional, Set

from .storage import SQLiteStorage
from .types import (
    EmbeddingProvider,
    FTSSearchResult,
    HybridConfig,
    SearchResult,
    VectorSearchResult,
)


class MemorySearcher:
    """Hybrid search engine - combines vector search and BM25 keyword search."""

    def __init__(
        self,
        storage: SQLiteStorage,
        embedding_provider: EmbeddingProvider,
        hybrid_config: Optional[HybridConfig] = None
    ):
        """
        Initialize searcher.

        Args:
            storage: SQLite storage instance
            embedding_provider: Embedding provider
            hybrid_config: Hybrid search configuration
        """
        self.storage = storage
        self.embedding = embedding_provider
        self.config = hybrid_config or HybridConfig()

    async def search(
        self,
        query: str,
        max_results: int = 10,
        min_score: Optional[float] = None,
        source_filter: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """
        Hybrid search.

        Args:
            query: Search query
            max_results: Maximum number of results
            min_score: Minimum score threshold
            source_filter: Filter by source types

        Returns:
            List of search results
        """
        if not query or not query.strip():
            return []

        min_score = min_score or self.config.min_score

        # Calculate number of candidates to fetch
        candidates = max_results * self.config.candidate_multiplier

        # Generate query embedding
        query_vec = await self.embedding.embed_query(query)

        # Perform searches in parallel
        vector_task = self._search_vectors_async(query_vec, candidates, source_filter)
        keyword_task = self._search_keywords_async(query, candidates, source_filter)

        vector_results, keyword_results = await asyncio.gather(
            vector_task,
            keyword_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(vector_results, Exception):
            vector_results = []
        if isinstance(keyword_results, Exception):
            keyword_results = []

        # Merge results
        merged = self._merge_results(vector_results, keyword_results)

        # Filter by min_score and limit
        filtered = [r for r in merged if r.score >= min_score]
        filtered = filtered[:max_results]

        # Enrich results with full chunk data
        return self._enrich_results(filtered)

    def search_sync(
        self,
        query: str,
        max_results: int = 10,
        min_score: Optional[float] = None,
        source_filter: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Synchronous version of search."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self.search(query, max_results, min_score, source_filter)
            )
        except RuntimeError:
            # No event loop
            return asyncio.run(
                self.search(query, max_results, min_score, source_filter)
            )

    async def _search_vectors_async(
        self,
        query_vec: List[float],
        limit: int,
        source_filter: Optional[List[str]] = None
    ) -> List[VectorSearchResult]:
        """Search vectors asynchronously."""
        # This is actually synchronous in the storage layer
        return self.storage.search_vectors(query_vec, limit, source_filter)

    async def _search_keywords_async(
        self,
        query: str,
        limit: int,
        source_filter: Optional[List[str]] = None
    ) -> List[FTSSearchResult]:
        """Search keywords asynchronously."""
        # This is actually synchronous in the storage layer
        return self.storage.search_fts(query, limit, source_filter)

    def _merge_results(
        self,
        vector_results: List[VectorSearchResult],
        keyword_results: List[FTSSearchResult]
    ) -> List[SearchResult]:
        """
        Merge vector and keyword search results.

        Algorithm:
        - Use chunk_id as key to merge
        - Weighted score: score = vector_weight * vector_score + text_weight * text_score
        - Unmatched result types get score of 0 for that component
        """
        # Build result map
        result_map: Dict[str, Dict[str, any]] = {}

        # Add vector results
        for vr in vector_results:
            result_map[vr.chunk_id] = {
                'chunk_id': vr.chunk_id,
                'vector_score': vr.score,
                'text_score': 0.0
            }

        # Add keyword results
        for kr in keyword_results:
            if kr.chunk_id in result_map:
                result_map[kr.chunk_id]['text_score'] = kr.score
            else:
                result_map[kr.chunk_id] = {
                    'chunk_id': kr.chunk_id,
                    'vector_score': 0.0,
                    'text_score': kr.score
                }

        # Calculate weighted scores
        merged = []
        for item in result_map.values():
            weighted_score = (
                self.config.vector_weight * item['vector_score'] +
                self.config.text_weight * item['text_score']
            )

            merged.append(SearchResult(
                chunk_id=item['chunk_id'],
                path="",
                source="",
                text="",
                snippet="",
                score=weighted_score,
                start_line=0,
                end_line=0
            ))

        # Sort by score descending
        merged.sort(key=lambda x: x.score, reverse=True)

        return merged

    def _enrich_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Enrich search results with full chunk data."""
        enriched = []

        for result in results:
            chunk = self.storage.get_chunk_by_id(result.chunk_id)

            if chunk:
                # Generate snippet (first 200 chars)
                snippet = chunk.text[:200].replace('\n', ' ')
                if len(chunk.text) > 200:
                    snippet += "..."

                enriched.append(SearchResult(
                    chunk_id=result.chunk_id,
                    path=chunk.path,
                    source=chunk.source,
                    text=chunk.text,
                    snippet=snippet,
                    score=result.score,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line
                ))
            else:
                # Chunk not found, keep original result
                enriched.append(result)

        return enriched

    def get_unique_sources(self) -> Set[str]:
        """Get all unique sources in the database."""
        files = self.storage.get_all_files()
        return set(f[1] for f in files)

    def search_by_source(
        self,
        query: str,
        source: str,
        max_results: int = 10
    ) -> List[SearchResult]:
        """Search within a specific source."""
        return self.search_sync(query, max_results, source_filter=[source])
