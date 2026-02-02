# -*- coding: utf-8 -*-
"""
文档管理模块

负责文档的完整生命周期管理：加载、切分、去重、存储、导出
"""

import os
import json
import time
import re
from typing import List, Dict, Optional, Any

from ..utils import DocumentLoader, TextSplitter


class DocumentManager:
    """
    文档管理模块

    负责文档的完整生命周期管理
    """

    def __init__(
        self,
        memory_manager,
        document_loader: Optional[DocumentLoader] = None,
        text_splitter: Optional[TextSplitter] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化文档管理器

        Args:
            memory_manager: MemoryManager 实例
            document_loader: 文档加载器（可选）
            text_splitter: 文本切分器（可选）
            config: 配置字典，包含：
                - similarity_threshold: 相似度阈值（默认0.85）
                - save_chunks: 是否保存切分结果（默认False）
                - chunks_dir: 切分结果保存目录
        """
        from ..core.memory import MemoryManager

        if not isinstance(memory_manager, MemoryManager):
            raise TypeError("memory_manager must be an instance of MemoryManager")

        self.memory_manager = memory_manager
        self.document_loader = document_loader or DocumentLoader()
        self.text_splitter = text_splitter or TextSplitter()
        self.config = config or {}

        # 默认配置
        self.similarity_threshold = self.config.get("similarity_threshold", 0.85)
        self.save_chunks = self.config.get("save_chunks", False)
        self.chunks_dir = self.config.get("chunks_dir", "~/.bitwiseai/chunks")

    def load_documents(
        self,
        folder_path: str,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        加载文件夹中的所有文档

        Args:
            folder_path: 文件夹路径
            skip_duplicates: 是否跳过重复文档

        Returns:
            包含统计信息的字典：
                - total: 总文档片段数
                - inserted: 实际插入的片段数
                - skipped: 跳过的重复片段数
        """
        if not folder_path:
            return {"total": 0, "inserted": 0, "skipped": 0}

        # 1. 加载文档
        documents = self.document_loader.load_folder(folder_path)

        if not documents:
            return {"total": 0, "inserted": 0, "skipped": 0}

        # 2. 切分文档
        chunks_with_metadata = []
        for doc in documents:
            chunks = self.text_splitter.split(doc["content"])

            # 提取文档名（去掉路径和扩展名）
            file_path = doc["file_path"]
            file_name = os.path.splitext(os.path.basename(file_path))[0]

            # 提取文档名关键词
            file_name_keywords = self._extract_filename_keywords(file_name)

            for idx, chunk in enumerate(chunks):
                chunks_with_metadata.append({
                    "text": chunk,
                    "source_file": file_path,
                    "file_name": file_name,
                    "file_name_keywords": file_name_keywords,
                    "file_hash": doc["file_hash"],
                    "chunk_index": idx,
                    "chunk_total": len(chunks),
                    "timestamp": doc["timestamp"],
                    "text_length": len(chunk)
                })

        total_chunks = len(chunks_with_metadata)

        # 3. 去重（如果启用）
        if skip_duplicates and total_chunks > 0:
            chunks_with_metadata = self._deduplicate_chunks(chunks_with_metadata)

        skipped_count = total_chunks - len(chunks_with_metadata)

        # 4. 存储到记忆系统
        inserted_count = 0
        if chunks_with_metadata:
            print(f"📚 开始处理 {len(chunks_with_metadata)} 个文档片段...")

            for chunk_data in chunks_with_metadata:
                # 使用 MemoryManager 索引文档
                result = self.memory_manager.index_document(
                    doc_path=chunk_data["source_file"],
                    content=chunk_data["text"]
                )
                if result.success:
                    inserted_count += 1

            print(f"✅ 成功插入 {inserted_count} 个文档片段到记忆系统")

        # 5. 可选：保存切分结果
        if self.save_chunks and chunks_with_metadata:
            self._save_chunks(chunks_with_metadata)

        return {
            "total": total_chunks,
            "inserted": inserted_count,
            "skipped": skipped_count
        }

    def add_text(
        self,
        text: str,
        source: Optional[str] = None,
        skip_duplicates: bool = True
    ) -> int:
        """
        添加单个文本到记忆系统

        Args:
            text: 文本内容
            source: 源标识（可选）
            skip_duplicates: 是否跳过重复

        Returns:
            插入的片段数量
        """
        if not text or not text.strip():
            return 0

        # 切分文本
        chunks = self.text_splitter.split(text)

        if not chunks:
            return 0

        # 准备元数据
        current_time = time.time()

        # 提取文档名和关键词
        if source:
            file_name = os.path.splitext(os.path.basename(source))[0]
            file_name_keywords = self._extract_filename_keywords(file_name)
        else:
            file_name = ""
            file_name_keywords = ""

        inserted_count = 0

        for idx, chunk in enumerate(chunks):
            chunk_data = {
                "text": chunk,
                "source_file": source or "",
                "file_name": file_name,
                "file_name_keywords": file_name_keywords,
                "file_hash": "",
                "chunk_index": idx,
                "chunk_total": len(chunks),
                "timestamp": current_time,
                "text_length": len(chunk)
            }

            # 使用 MemoryManager 索引
            result = self.memory_manager.index_document(
                doc_path=source or f"text_{int(time.time())}_{idx}",
                content=chunk
            )
            if result.success:
                inserted_count += 1

        return inserted_count

    def _deduplicate_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        基于搜索相似度去重

        Args:
            chunks: 文档片段列表

        Returns:
            去重后的文档片段列表
        """
        if not chunks:
            return []

        # 使用 MemoryManager 的搜索功能检查重复
        unique_chunks = []

        for chunk in chunks:
            # 搜索相似内容
            results = self.memory_manager.search_sync(
                query=chunk["text"][:200],  # 搜索前200字符
                max_results=1
            )

            # 如果找到高相似度结果，则跳过
            if results and results[0].score >= self.similarity_threshold:
                continue

            unique_chunks.append(chunk)

        return unique_chunks

    def check_duplicates(self, texts: List[str]) -> List[bool]:
        """
        检查文本列表中的重复项

        Args:
            texts: 文本列表

        Returns:
            布尔列表，True表示重复
        """
        if not texts:
            return []

        is_duplicate = []

        for text in texts:
            # 搜索相似内容
            results = self.memory_manager.search_sync(
                query=text[:200],
                max_results=1
            )

            # 如果找到高相似度结果，则标记为重复
            if results and results[0].score >= self.similarity_threshold:
                is_duplicate.append(True)
            else:
                is_duplicate.append(False)

        return is_duplicate

    def export_documents(
        self,
        output_dir: str,
        format: str = "separate_md"
    ) -> int:
        """
        从记忆系统导出文档为MD格式

        Args:
            output_dir: 输出目录
            format: 导出格式（"separate_md": 按源文件分别导出）

        Returns:
            导出的文件数量
        """
        if format != "separate_md":
            raise ValueError(f"不支持的导出格式: {format}")

        # 确保输出目录存在
        output_dir = os.path.expanduser(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        try:
            # 获取所有文档源
            from ..core.memory import MemorySource
            results = self.memory_manager.search_sync(
                query="*",
                max_results=10000,
                source_filter=[MemorySource.DOCS]
            )

            if not results:
                return 0

            # 按源文件分组
            files_dict = {}
            for item in results:
                source_file = item.path
                if source_file not in files_dict:
                    files_dict[source_file] = []

                files_dict[source_file].append({
                    "text": item.text,
                    "chunk_id": item.chunk_id
                })

            # 按源文件导出
            exported_count = 0
            for source_file, chunks in files_dict.items():
                # 生成输出文件名
                if source_file and source_file != "unknown":
                    base_name = os.path.basename(source_file)
                    if not base_name.endswith(".md"):
                        base_name = base_name.rsplit(".", 1)[0] + ".md"
                else:
                    base_name = f"document_{exported_count + 1}.md"

                output_path = os.path.join(output_dir, base_name)

                # 合并chunks并写入文件
                content = "\n\n".join([chunk["text"] for chunk in chunks])
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)

                exported_count += 1

            return exported_count
        except Exception as e:
            print(f"⚠️  导出文档失败: {e}")
            return 0

    def get_document_stats(self) -> Dict[str, Any]:
        """
        获取文档统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = self.memory_manager.stats()
            return {
                "total_chunks": stats.total_chunks,
                "total_files": stats.total_files,
                "db_size_bytes": stats.db_size_bytes
            }
        except Exception as e:
            print(f"⚠️  获取统计信息失败: {e}")
            return {"total_chunks": 0, "total_files": 0, "db_size_bytes": 0}

    def _extract_filename_keywords(self, file_name: str) -> str:
        """
        提取文档名关键词

        Args:
            file_name: 文档名（不含扩展名）

        Returns:
            关键词字符串（用空格分隔）
        """
        if not file_name:
            return ""

        # 尝试使用jieba分词（如果可用）
        try:
            import jieba
            words = jieba.cut(file_name)
            stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '如果', '如何', '什么', '哪个', '哪些'}
            keywords = [w for w in words if w not in stop_words and len(w) > 1]
            return " ".join(keywords)
        except ImportError:
            text = re.sub(r'[_\-\s]+', ' ', file_name)
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            words = [w for w in text.split() if len(w) > 1]
            return " ".join(words)

    def _save_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        保存切分结果到文件（可选功能）

        Args:
            chunks: 文档片段列表
        """
        if not chunks:
            return

        chunks_dir = os.path.expanduser(self.chunks_dir)
        os.makedirs(chunks_dir, exist_ok=True)

        # 按源文件分组保存
        files_dict = {}
        for chunk in chunks:
            source_file = chunk.get("source_file", "unknown")
            if source_file not in files_dict:
                files_dict[source_file] = []

            files_dict[source_file].append(chunk)

        # 保存每个文件的chunks
        for source_file, file_chunks in files_dict.items():
            if source_file and source_file != "unknown":
                base_name = os.path.basename(source_file)
                json_name = base_name.rsplit(".", 1)[0] + "_chunks.json"
            else:
                json_name = f"chunks_{int(time.time())}.json"

            json_path = os.path.join(chunks_dir, json_name)

            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(file_chunks, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️  保存切分结果失败 {json_path}: {e}")


__all__ = ["DocumentManager"]
