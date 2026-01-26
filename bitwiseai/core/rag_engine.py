# -*- coding: utf-8 -*-
"""
RAG 引擎

独立的 RAG 引擎，封装向量数据库操作，不依赖 skills
"""
from typing import List, Optional, Dict, Any
from ..vector_database import MilvusDB
from ..utils import DocumentLoader, TextSplitter
from .document_manager import DocumentManager
from .document_matcher import DocumentNameMatcher


class RAGEngine:
    """
    RAG 引擎

    提供文档加载、检索、管理功能
    作为RAG流程编排器，调用DocumentManager和MilvusDB
    """

    def __init__(
        self,
        vector_db: MilvusDB,
        document_manager: Optional[DocumentManager] = None,
        document_loader: Optional[DocumentLoader] = None,
        text_splitter: Optional[TextSplitter] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 RAG 引擎

        Args:
            vector_db: 向量数据库实例
            document_manager: 文档管理器（可选，如果不提供则自动创建）
            document_loader: 文档加载器（可选，用于创建DocumentManager）
            text_splitter: 文本切分器（可选，用于创建DocumentManager）
            config: 配置字典（可选，用于创建DocumentManager）
        """
        self.vector_db = vector_db
        self.config = config or {}
        
        # 创建或使用提供的DocumentManager
        if document_manager is not None:
            self.document_manager = document_manager
        else:
            self.document_manager = DocumentManager(
                vector_db=vector_db,
                document_loader=document_loader,
                text_splitter=text_splitter,
                config=config or {}
            )
        
        # 文档名匹配器（延迟初始化）
        self.document_matcher: Optional[DocumentNameMatcher] = None
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
        添加单个文本到向量数据库（委托给DocumentManager）

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
        搜索相关文档（调用MilvusDB混合检索）
        
        支持两阶段检索：先匹配文档名，再在匹配的文档范围内检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_hybrid: 是否使用混合检索

        Returns:
            检索到的文档内容（用换行符连接）
        """
        # 使用search_with_metadata获取结果（包含文档名匹配逻辑），然后提取文本
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
        
        支持两阶段检索：先匹配文档名，再在匹配的文档范围内检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            use_hybrid: 是否使用混合检索

        Returns:
            检索结果列表，每个元素包含text和元数据
        """
        # 文档名匹配（如果启用）
        filter_expr = None
        if self.enable_document_name_matching:
            # 初始化文档名匹配器（如果未初始化）
            if self.document_matcher is None:
                self.document_matcher = DocumentNameMatcher(
                    vector_db=self.vector_db,
                    match_threshold=self.document_name_match_threshold
                )
            
            # 匹配文档名
            matched_files = self.document_matcher.match_documents(query)
            
            if matched_files:
                # 构建Milvus filter表达式
                # Milvus filter语法：使用 in 操作符，字符串需要用单引号
                # 转义文件路径中的特殊字符（单引号需要转义）
                escaped_files = [f"'{f.replace("'", "\\'")}'" for f in matched_files]
                filter_expr = f'source_file in [{",".join(escaped_files)}]'
                print(f"🔍 使用文档名过滤，限制在 {len(matched_files)} 个文档中检索")
        
        # 执行检索（带filter）
        if use_hybrid:
            return self.vector_db.hybrid_search(query, top_k=top_k, use_keyword=True, filter_expr=filter_expr)
        else:
            return self.vector_db.search_with_metadata(query, top_k=top_k, filter_expr=filter_expr)

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
        清空向量数据库
        """
        self.vector_db.clear()

    def count(self) -> int:
        """
        获取文档数量

        Returns:
            文档数量
        """
        return self.vector_db.count()

    def get_document_stats(self) -> Dict[str, Any]:
        """
        获取文档统计信息

        Returns:
            统计信息字典
        """
        return self.document_manager.get_document_stats()

    @property
    def collection_name(self) -> str:
        """获取集合名称"""
        return self.vector_db.collection_name

    @property
    def db_file(self) -> str:
        """获取数据库文件路径"""
        return self.vector_db.db_file


__all__ = ["RAGEngine"]

