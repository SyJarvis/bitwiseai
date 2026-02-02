# -*- coding: utf-8 -*-
"""
RAG 引擎

独立的 RAG 引擎，封装记忆系统操作，不依赖 skills
"""

from typing import List, Optional, Dict, Any
from ..utils import DocumentLoader, TextSplitter
from .document_manager import DocumentManager


class RAGEngine:
    """
    RAG 引擎

    提供文档加载、检索、管理功能
    作为RAG流程编排器，调用DocumentManager和MemoryManager
    """

    def __init__(
        self,
        memory_manager,
        document_manager: Optional[DocumentManager] = None,
        document_loader: Optional[DocumentLoader] = None,
        text_splitter: Optional[TextSplitter] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 RAG 引擎

        Args:
            memory_manager: MemoryManager 实例
            document_manager: 文档管理器（可选，如果不提供则自动创建）
            document_loader: 文档加载器（可选，用于创建DocumentManager）
            text_splitter: 文本切分器（可选，用于创建DocumentManager）
            config: 配置字典（可选，用于创建DocumentManager）
        """
        from ..core.memory import MemoryManager

        if not isinstance(memory_manager, MemoryManager):
            raise TypeError("memory_manager must be an instance of MemoryManager")

        self.memory_manager = memory_manager
        self.config = config or {}

        # 创建或使用提供的DocumentManager
        if document_manager is not None:
            self.document_manager = document_manager
        else:
            self.document_manager = DocumentManager(
                memory_manager=memory_manager,
                document_loader=document_loader,
                text_splitter=text_splitter,
                config=config or {}
            )

        # 配置
        self.enable_document_name_matching = self.config.get("enable_document_name_matching", True)
        self.document_name_match_threshold = self.config.get("document_name_match_threshold", 0.3)

    def load_documents(self, folder_path: str, skip_duplicates: bool = True) -> Dict[str, Any]:
        """
        加载文件夹中的所有文档（委托给DocumentManager）

        Args:
            folder_path: 文件夹路径
            skip_duplicates: 是否跳过重复文档

        Returns:
            包含统计信息的字典：
                - total: 总文档片段数
                - inserted: 实际插入的片段数
                - skipped: 跳过的重复片段数
        """
        return self.document_manager.load_documents(folder_path, skip_duplicates=skip_duplicates)

    def add_text(self, text: str, source: Optional[str] = None, skip_duplicates: bool = True) -> int:
        """
        添加单个文本到记忆系统（委托给DocumentManager）

        Args:
            text: 文本内容
            source: 源标识（可选）
            skip_duplicates: 是否跳过重复

        Returns:
            插入的片段数量
        """
        return self.document_manager.add_text(text, source=source, skip_duplicates=skip_duplicates)

    def search(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> str:
        """
        搜索相关文档

        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_hybrid: 是否使用混合检索（保留参数用于兼容性）

        Returns:
            检索到的文档内容（用换行符连接）
        """
        # 使用search_with_metadata获取结果，然后提取文本
        results = self.search_with_metadata(query, top_k=top_k, use_hybrid=use_hybrid)
        return "\n".join([r["text"] for r in results])

    def search_with_metadata(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        搜索相关文档（返回元数据）

        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_hybrid: 是否使用混合检索（保留参数用于兼容性，MemoryManager 始终使用混合搜索）

        Returns:
            检索结果列表，每个元素包含text和元数据
        """
        # 使用 MemoryManager 搜索
        results = self.memory_manager.search_sync(
            query=query,
            max_results=top_k,
            source_filter=["docs"]  # 只搜索文档
        )

        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                "text": result.text,
                "source_file": result.path,
                "score": result.score,
                "start_line": result.start_line,
                "end_line": result.end_line,
                "chunk_id": result.chunk_id
            })

        return formatted_results

    def export_documents(self, output_dir: str, format: str = "separate_md") -> int:
        """
        导出文档（委托给DocumentManager）

        Args:
            output_dir: 输出目录
            format: 导出格式

        Returns:
            导出的文件数量
        """
        return self.document_manager.export_documents(output_dir, format=format)

    def clear(self):
        """
        清空记忆系统中的文档
        """
        # Get all docs and remove them
        from ..core.memory import MemorySource
        results = self.memory_manager.search_sync(
            query="",
            max_results=10000,
            source_filter=[MemorySource.DOCS]
        )

        # Track unique paths to remove
        paths_to_remove = set()
        for result in results:
            paths_to_remove.add(result.path)

        # Remove each path
        for path in paths_to_remove:
            self.memory_manager.remove_index(path)

    def count(self) -> int:
        """
        获取文档数量

        Returns:
            文档数量
        """
        stats = self.memory_manager.stats()
        return stats.total_chunks

    def get_document_stats(self) -> Dict[str, Any]:
        """
        获取文档统计信息

        Returns:
            统计信息字典
        """
        return self.document_manager.get_document_stats()

    @property
    def collection_name(self) -> str:
        """获取集合名称（保留属性用于兼容性）"""
        return "docs"

    @property
    def db_file(self) -> str:
        """获取数据库文件路径"""
        return str(self.memory_manager.storage.db_path)


__all__ = ["RAGEngine"]
