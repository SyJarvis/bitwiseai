# -*- coding: utf-8 -*-
"""
文档管理模块

负责文档的完整生命周期管理：加载、切分、去重、存储、导出
"""
import os
import json
import time
from typing import List, Dict, Optional, Any
from ..vector_database import MilvusDB
from ..utils import DocumentLoader, TextSplitter


class DocumentManager:
    """
    文档管理模块

    负责文档的完整生命周期管理
    """

    def __init__(
        self,
        vector_db: MilvusDB,
        document_loader: Optional[DocumentLoader] = None,
        text_splitter: Optional[TextSplitter] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化文档管理器

        Args:
            vector_db: 向量数据库实例
            document_loader: 文档加载器（可选）
            text_splitter: 文本切分器（可选）
            config: 配置字典，包含：
                - similarity_threshold: 相似度阈值（默认0.85）
                - save_chunks: 是否保存切分结果（默认False）
                - chunks_dir: 切分结果保存目录
        """
        self.vector_db = vector_db
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
            for idx, chunk in enumerate(chunks):
                chunks_with_metadata.append({
                    "text": chunk,
                    "source_file": doc["file_path"],
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

        # 4. 存储到向量数据库
        inserted_count = 0
        if chunks_with_metadata:
            texts = [c["text"] for c in chunks_with_metadata]
            metadata = [
                {
                    "source_file": c["source_file"],
                    "file_hash": c["file_hash"],
                    "chunk_index": c["chunk_index"],
                    "chunk_total": c["chunk_total"],
                    "timestamp": c["timestamp"],
                    "text_length": c["text_length"]
                }
                for c in chunks_with_metadata
            ]
            inserted_count = self.vector_db.add_texts_with_metadata(texts, metadata)

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
        添加单个文本到向量数据库

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
        chunks_with_metadata = []
        current_time = time.time()
        for idx, chunk in enumerate(chunks):
            chunks_with_metadata.append({
                "text": chunk,
                "source_file": source or "",
                "file_hash": "",
                "chunk_index": idx,
                "chunk_total": len(chunks),
                "timestamp": current_time,
                "text_length": len(chunk)
            })

        # 去重（如果启用）
        if skip_duplicates:
            chunks_with_metadata = self._deduplicate_chunks(chunks_with_metadata)

        # 存储到向量数据库
        if chunks_with_metadata:
            texts = [c["text"] for c in chunks_with_metadata]
            metadata = [
                {
                    "source_file": c["source_file"],
                    "file_hash": c["file_hash"],
                    "chunk_index": c["chunk_index"],
                    "chunk_total": c["chunk_total"],
                    "timestamp": c["timestamp"],
                    "text_length": c["text_length"]
                }
                for c in chunks_with_metadata
            ]
            return self.vector_db.add_texts_with_metadata(texts, metadata)

        return 0

    def _deduplicate_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        基于嵌入向量相似度去重

        Args:
            chunks: 文档片段列表

        Returns:
            去重后的文档片段列表
        """
        if not chunks:
            return []

        # 生成嵌入向量
        texts = [c["text"] for c in chunks]
        try:
            vectors = self.vector_db.embedding_model.embed_documents(texts)
        except Exception as e:
            print(f"⚠️  生成嵌入向量失败: {e}")
            return chunks  # 如果失败，返回原始列表

        # 在Milvus中搜索相似向量
        threshold = self.similarity_threshold
        try:
            similar_results = self.vector_db.search_similar_vectors(
                vectors, threshold, top_k=1
            )

            # 过滤重复的chunks
            unique_chunks = []
            for i, chunk in enumerate(chunks):
                # 如果没有找到相似结果，或者相似度低于阈值，则保留
                if not similar_results[i] or len(similar_results[i]) == 0:
                    unique_chunks.append(chunk)
                else:
                    # 检查最高相似度是否低于阈值
                    max_similarity = max([r["score"] for r in similar_results[i]], default=0.0)
                    if max_similarity < threshold:
                        unique_chunks.append(chunk)
                    # 否则跳过（重复）

            return unique_chunks
        except Exception as e:
            print(f"⚠️  去重检查失败: {e}")
            return chunks  # 如果失败，返回原始列表

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

        # 生成嵌入向量
        try:
            vectors = self.vector_db.embedding_model.embed_documents(texts)
        except Exception as e:
            print(f"⚠️  生成嵌入向量失败: {e}")
            return [False] * len(texts)

        # 搜索相似向量
        threshold = self.similarity_threshold
        try:
            similar_results = self.vector_db.search_similar_vectors(
                vectors, threshold, top_k=1
            )

            # 返回是否重复
            is_duplicate = []
            for results in similar_results:
                if results and len(results) > 0:
                    max_similarity = max([r["score"] for r in results], default=0.0)
                    is_duplicate.append(max_similarity >= threshold)
                else:
                    is_duplicate.append(False)

            return is_duplicate
        except Exception as e:
            print(f"⚠️  重复检查失败: {e}")
            return [False] * len(texts)

    def export_documents(
        self,
        output_dir: str,
        format: str = "separate_md"
    ) -> int:
        """
        从向量数据库导出文档为MD格式

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

        # 从向量数据库获取所有文档
        try:
            # 查询所有文档（限制数量以避免内存问题）
            query_result = self.vector_db.client.query(
                collection_name=self.vector_db.collection_name,
                filter="",
                limit=10000,  # 限制查询数量
                output_fields=["text", "source_file", "file_hash", "chunk_index", "chunk_total"]
            )

            if not query_result:
                return 0

            # 按源文件分组
            files_dict = {}
            for item in query_result:
                source_file = item.get("source_file", "unknown")
                if source_file not in files_dict:
                    files_dict[source_file] = []

                files_dict[source_file].append({
                    "text": item.get("text", ""),
                    "chunk_index": item.get("chunk_index", 0),
                    "chunk_total": item.get("chunk_total", 1)
                })

            # 按源文件导出
            exported_count = 0
            for source_file, chunks in files_dict.items():
                # 按chunk_index排序
                chunks.sort(key=lambda x: x["chunk_index"])

                # 生成输出文件名
                if source_file and source_file != "unknown":
                    # 使用源文件名
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
            count = self.vector_db.count()
            return {
                "total_chunks": count,
                "collection_name": self.vector_db.collection_name,
                "db_file": self.vector_db.db_file
            }
        except Exception as e:
            print(f"⚠️  获取统计信息失败: {e}")
            return {"total_chunks": 0, "collection_name": "", "db_file": ""}

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
            # 生成文件名
            if source_file and source_file != "unknown":
                base_name = os.path.basename(source_file)
                json_name = base_name.rsplit(".", 1)[0] + "_chunks.json"
            else:
                json_name = f"chunks_{int(time.time())}.json"

            json_path = os.path.join(chunks_dir, json_name)

            # 保存为JSON
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(file_chunks, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"⚠️  保存切分结果失败 {json_path}: {e}")


__all__ = ["DocumentManager"]

